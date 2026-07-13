"""Import pipeline for the Irancell job-profile master workbook.

Tuned to the real structure of data/job_profiles_master.xlsm:
  * Sheet "Job_Profile_Data": header on row 8, one parsed Word document per
    row with the official template sections as columns.
  * Sheet "Sheet1": department -> division-code mapping.

Parsing rules mirror how the source Word documents were flattened:
  * Technical competencies come as "Title Type Level" streams where Type is
    one of the Irancell knowledge categories and Level one of the mastery
    levels — we re-split the stream on those anchors.
  * Behavioral competencies are bullet lists (old "Leadership/Innovation..."
    vitals or the current "Live Y'ello" values).
  * Collaboration is a "Direct Reports: ... Matrix Reports to: ... Key
    Customers: ... Key Suppliers: ..." record.
  * Levels normalize to the Irancell grade codes 1, 2, 2H, 3, 3H, 4, 5.
"""
from __future__ import annotations

import re
from datetime import datetime

import openpyxl
from sqlalchemy.orm import Session

from .. import models

HEADER_ROW = 8

COMP_TYPES = ["General Business Knowledge", "Functional Knowledge", "Specialized Knowledge"]
COMP_LEVELS = ["Basic", "Intermediate", "Advanced", "Advance", "Expert", "Foundational"]
GRADE_ORDER = ["1", "2", "2H", "3", "3H", "4", "5"]

DIVISION_NAMES = {
    "NWG": "Network Group",
    "S&D": "Sales & Distribution",
    "FIN": "Finance",
    "MKT": "Marketing",
    "CPG": "Capital Program Group",
    "IT": "Information Technology",
    "ITS": "IT Services",
    "CR": "Customer Relations",
    "EB": "Enterprise Business",
    "HR": "Human Resources",
    "CTIO": "CTIO Office",
    "A&R": "Audit & Risk",
    "L&R": "Legal & Regulatory",
    "DG": "Digital",
    "VM": "Vista Media",
    "SC": "Supply Chain Management",
    "PROC": "Procurement",
    "LABs": "Irancell Labs",
    "CA": "Corporate Affairs",
    "S&T": "Strategy & Transformation",
    "FX": "FanavaranTose'e (FX)",
    "CM": "Commercial",
    "CT": "Corporate Technology",
    "IFM": "Infrastructure & Facility Management",
    "TQM": "Total Quality Management",
    "VI": "Vestapart Idea",
    "CEI": "Customer Experience & Insight",
    "COO": "COO Office",
    "BRM": "Business Relationship Management",
}


def clean(value) -> str:
    if value is None:
        return ""
    text = str(value)
    text = text.replace("_x000B_", "\n").replace("_x000C_", "\n").replace("\x0b", "\n").replace("\x0c", "\n")
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_grade(raw) -> str | None:
    text = clean(raw).upper().replace("L", "")
    if text in {"", "-", "NONE", "TBD", "N/A", "#N/A"}:
        return None
    if text in {"CONTRACTOR", "CONSULTANT"}:
        return None
    text = text.replace(" ", "")
    if text in {g.upper() for g in GRADE_ORDER}:
        return "2H" if text == "2H" else ("3H" if text == "3H" else text)
    return None


def parse_int(raw) -> int:
    text = clean(raw)
    match = re.search(r"\d+", text)
    return int(match.group()) if match else 0


def parse_date(raw) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw
    text = clean(raw)
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def parse_technical_competencies(raw: str) -> list[dict]:
    """Split the flattened 'Title Type Level' stream into structured rows."""
    text = clean(raw)
    if not text:
        return []
    # Drop leading table-header noise ("Title Type Level", "Competency Name ...", "Row", "Item")
    text = re.sub(
        r"^(Competency Name Competency Type Competency Level|Title Type Level|Item Type Level|Row Title Type Level)\s*",
        "",
        text,
        flags=re.I,
    )
    type_pattern = "|".join(re.escape(t) for t in COMP_TYPES)
    level_pattern = "|".join(re.escape(lv) for lv in COMP_LEVELS)
    results = []
    for match in re.finditer(
        rf"(.+?)\s+({type_pattern})\s+({level_pattern})d?\b", text, flags=re.I
    ):
        title = match.group(1).strip(" .,;:-••")
        title = re.sub(r"^\d+\s+", "", title)  # numbered rows ("1 Opex Management ...")
        if not title or len(title) > 120:
            title = title[-120:].strip() if title else ""
        if title:
            level = match.group(3).capitalize()
            if level == "Advance":
                level = "Advanced"
            results.append(
                {"name": title, "category": match.group(2).title(), "required_level": level}
            )
    return results


def parse_behavioral_competencies(raw: str) -> list[str]:
    text = clean(raw)
    if not text:
        return []
    parts = re.split(r"[\n••]+", text)
    known = [
        "Lead with Care",
        "Collaborate with Agility",
        "Act with Inclusion",
        "Serve with Respect",
        "Can-do with Integrity",
        "Get it Done",
        "Complete Accountability",
        "Leadership",
        "Innovation",
        "Relationship",
        "Integrity",
        "Can-do",
        "Customer Centricity",
        "Agility",
        "Execution",
        "Coaching",
        "Operational Decision Making",
    ]
    found: list[str] = []
    # First pass: bullet-split items
    for part in parts:
        item = part.strip(" .,-")
        if 2 < len(item) <= 60:
            found.append(item)
    if found:
        # dedupe, keep order
        seen = set()
        return [x for x in found if not (x.lower() in seen or seen.add(x.lower()))]
    # Fallback: scan the run-on string for known values
    lower = text.lower()
    return [k for k in known if k.lower() in lower]


def parse_collaboration(raw: str) -> dict:
    text = clean(raw)
    result = {"direct_reports": "", "matrix_reports": "", "key_customers": "", "key_suppliers": "", "relations": ""}
    if not text:
        return result
    anchors = [
        ("direct_reports", r"Direct Reports?\s*:"),
        ("matrix_reports", r"Matrix Reports?( to)?\s*:"),
        ("key_customers", r"Key Customers?\s*:"),
        ("key_suppliers", r"Key Suppliers?\s*:"),
        ("relations", r"Relations?[ ,]*(etc\.?)?\s*:"),
    ]
    positions = []
    for key, pattern in anchors:
        match = re.search(pattern, text, flags=re.I)
        if match:
            positions.append((match.start(), match.end(), key))
    positions.sort()
    for i, (_start, end, key) in enumerate(positions):
        stop = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        result[key] = text[end:stop].strip(" .,;")
    if not positions:
        result["relations"] = text
    return result


def split_sentences(raw: str) -> list[str]:
    """Split a responsibilities blob into individual statements."""
    text = clean(raw)
    if not text:
        return []
    parts = re.split(r"(?:\n+|(?<=[.;])\s+(?=[A-Z“\"']))", text)
    return [p.strip(" .;••-") for p in parts if len(p.strip()) > 8]


# ------------------------------------------------------------- db helpers
def get_or_create(db: Session, model, defaults: dict | None = None, **kwargs):
    instance = db.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    instance = model(**kwargs, **(defaults or {}))
    db.add(instance)
    db.flush()
    return instance


def ensure_grades(db: Session):
    bands = {
        "1": "Support",
        "2": "Professional",
        "2H": "Senior Professional",
        "3": "Specialist / Senior Specialist / Manager",
        "3H": "Lead Specialist / Senior Manager",
        "4": "General Manager / Executive",
        "5": "C-Level",
    }
    for rank, code in enumerate(GRADE_ORDER, start=1):
        get_or_create(db, models.Grade, defaults={"rank": rank, "band": bands.get(code, "")}, code=code)


def infer_role_family(title: str, division_code: str) -> str:
    """Role families derive from the division (Irancell's org architecture)."""
    return DIVISION_NAMES.get(division_code, division_code or "General")


def infer_job_family(title: str) -> str:
    """Job family from the title's functional stem (e.g. 'Access Transmission')."""
    t = clean(title)
    t = re.sub(r"\s*\(.*?\)\s*", " ", t)  # drop "(Vendor)" etc.
    stop = (
        r"General Manager|Senior Manager|Senior Specialist|Lead Specialist|Senior Engineer|"
        r"Team Leader|Team Lead|Manager|Specialist|Engineer|Analyst|Expert|Administrator|"
        r"Coordinator|Supervisor|Advisor|Officer|Agent|Lead|Head"
    )
    match = re.search(rf"^(.*?)\s*(?:{stop})\b", t, flags=re.I)
    stem = (match.group(1) if match else t).strip(" -–:&,")
    return stem if len(stem) >= 3 else t


def resolve_title(title_cell: str, source_file: str) -> str:
    """The workbook's title column is sometimes truncated mid-word (an
    artifact of flattening the Word documents). The source file name carries
    the full title, so prefer it when the cell looks like a cut prefix."""
    title = re.sub(r"\s+", " ", clean(title_cell)).strip()
    stem = re.sub(r"\.docx?$", "", clean(source_file), flags=re.I)
    stem = re.sub(r"\s+", " ", stem).strip()
    if not title:
        return stem
    if not stem:
        return title
    norm_title = title.lower().rstrip(" .")
    norm_stem = stem.lower()
    if norm_stem.startswith(norm_title) and len(title) < len(stem) - 2:
        return stem  # cell is a truncated prefix of the file name
    if len(title) < 0.6 * len(stem) and norm_title.split(" ")[0] == norm_stem.split(" ")[0]:
        return stem
    return title


ROW_COLUMNS = {
    "file_name": 0,
    "header_text": 1,
    "title": 3,
    "location": 4,
    "reports_to": 5,
    "subordinates": 6,
    "level": 7,
    "mission": 8,
    "context": 9,
    "responsibilities": 10,
    "collaboration": 11,
    "authorities": 12,
    "education": 13,
    "experience": 14,
    "technical": 15,
    "behavioral": 16,
    "trainings": 17,
    "working_condition": 18,
    "performance": 19,
    "signoff": 20,
    "division_approval": 21,
    "hr_approval": 22,
    "doc_version": 23,
    "approved_date": 28,
    "div": 31,
}


def import_workbook(db: Session, path: str, limit: int | None = None) -> dict:
    """Parse the master workbook and load it into the database. Idempotent by
    source file name (re-import updates instead of duplicating)."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["Job_Profile_Data"]

    ensure_grades(db)
    stats = {"created": 0, "updated": 0, "skipped": 0, "competencies": 0}
    seen_titles: dict[str, int] = {}

    existing_by_source = {
        p.source_file: p for p in db.query(models.JobProfile).filter(models.JobProfile.source_file != "").all()
    }

    for i, row in enumerate(ws.iter_rows(min_row=HEADER_ROW + 2, values_only=True)):
        if limit and stats["created"] + stats["updated"] >= limit:
            break
        c = {k: row[v] if v < len(row) else None for k, v in ROW_COLUMNS.items()}
        source_file = clean(c["file_name"])
        title = resolve_title(clean(c["title"]), source_file)
        if not title:
            continue
        if len(title) < 3:
            stats["skipped"] += 1
            continue

        division_code = clean(c["div"]).replace("#N/A", "").strip()
        grade_code = normalize_grade(c["level"])

        division = None
        if division_code:
            division = get_or_create(
                db,
                models.OrgUnit,
                defaults={"code": division_code},
                name=DIVISION_NAMES.get(division_code, division_code),
                unit_type="division",
            )
        department = None
        dept_name = clean(c["location"])
        if dept_name:
            department = get_or_create(
                db,
                models.OrgUnit,
                defaults={"code": division_code, "parent_id": division.id if division else None},
                name=dept_name[:250],
                unit_type="department",
            )

        role_family = get_or_create(db, models.RoleFamily, name=infer_role_family(title, division_code))
        job_family = get_or_create(
            db, models.JobFamily, defaults={"role_family_id": role_family.id}, name=infer_job_family(title)[:250]
        )
        grade = db.query(models.Grade).filter_by(code=grade_code).first() if grade_code else None

        collaboration = parse_collaboration(clean(c["collaboration"]))
        approved = parse_date(c["approved_date"])

        profile = existing_by_source.get(source_file)
        creating = profile is None
        if creating:
            profile = models.JobProfile(job_title=title[:250], source_file=source_file)
            db.add(profile)
        profile.job_title = title[:250]
        profile.job_code = f"IR-{division_code or 'GEN'}-{1000 + i}"
        profile.location = dept_name[:250]
        profile.reports_to = clean(c["reports_to"])[:250]
        profile.direct_reports = parse_int(c["subordinates"])
        profile.org_level = clean(c["level"])[:60]
        profile.grade_id = grade.id if grade else None
        profile.band = grade.band if grade else ""
        profile.role_family_id = role_family.id
        profile.job_family_id = job_family.id
        profile.division_id = division.id if division else None
        profile.department_id = department.id if department else None
        profile.mission = clean(c["mission"])
        profile.context = clean(c["context"])
        profile.responsibilities_text = clean(c["responsibilities"])
        profile.collaboration_text = clean(c["collaboration"])
        profile.collaboration = collaboration
        profile.authorities_text = clean(c["authorities"])
        profile.education_text = clean(c["education"])
        profile.experience_text = clean(c["experience"])
        profile.trainings_text = clean(c["trainings"])
        profile.behavioral_text = clean(c["behavioral"])
        profile.working_conditions = clean(c["working_condition"])
        profile.performance_standards = clean(c["performance"])
        profile.signoff = {
            "template": clean(c["signoff"]),
            "division_approval": clean(c["division_approval"]),
            "hr_approval": clean(c["hr_approval"]),
        }
        profile.document_version = clean(c["doc_version"])[:30] or "1.0"
        profile.approved_date = approved
        profile.status = "Published" if approved else "Draft"
        profile.is_active = True
        profile.job_category = "Managerial" if re.search(r"\bmanager\b|\bhead\b|\bdirector\b", title, re.I) else "Professional"

        db.flush()

        # Rebuild child rows on re-import
        if not creating:
            db.query(models.Responsibility).filter_by(profile_id=profile.id).delete()
            db.query(models.ProfileCompetency).filter_by(profile_id=profile.id).delete()
            db.query(models.Qualification).filter_by(profile_id=profile.id).delete()

        for order, statement in enumerate(split_sentences(clean(c["responsibilities"]))[:40]):
            db.add(models.Responsibility(profile_id=profile.id, text=statement, sort_order=order))

        for comp in parse_technical_competencies(clean(c["technical"])):
            competency = get_or_create(
                db,
                models.Competency,
                defaults={"category": comp["category"]},
                name=comp["name"][:250],
                comp_type="Technical",
            )
            db.add(
                models.ProfileCompetency(
                    profile_id=profile.id,
                    competency_id=competency.id,
                    required_level=comp["required_level"],
                    assessment_method="Interview / Technical Assessment",
                )
            )
            stats["competencies"] += 1

        for name in parse_behavioral_competencies(clean(c["behavioral"])):
            competency = get_or_create(db, models.Competency, name=name[:250], comp_type="Behavioral")
            db.add(
                models.ProfileCompetency(
                    profile_id=profile.id,
                    competency_id=competency.id,
                    required_level="Expected",
                    assessment_method="Behavioral Interview",
                )
            )

        if clean(c["education"]):
            db.add(models.Qualification(profile_id=profile.id, qual_type="education", text=clean(c["education"])))
        if clean(c["experience"]):
            db.add(models.Qualification(profile_id=profile.id, qual_type="experience", text=clean(c["experience"])))
        if clean(c["trainings"]):
            db.add(models.Qualification(profile_id=profile.id, qual_type="training", text=clean(c["trainings"])))

        seen_titles.setdefault(title.lower(), profile.id)
        stats["created" if creating else "updated"] += 1
        if (stats["created"] + stats["updated"]) % 200 == 0:
            db.commit()

    db.commit()
    build_career_paths(db)
    db.commit()
    return stats


LADDER = [
    ("engineer|analyst|coordinator|agent|officer|administrator", 0),
    ("specialist", 1),
    ("senior specialist|lead specialist|team leader|team lead|supervisor", 2),
    ("manager", 3),
    ("senior manager", 4),
    ("general manager|head", 5),
]


def ladder_rank(title: str) -> int:
    t = title.lower()
    best = -1
    for pattern, rank in LADDER:
        if re.search(rf"\b(?:{pattern})\b", t):
            best = max(best, rank)
    return best


def build_career_paths(db: Session):
    """Derive career ladder edges: same job family, ascending ladder rank."""
    db.query(models.CareerPath).delete()
    profiles = db.query(models.JobProfile).filter(models.JobProfile.job_family_id.isnot(None)).all()
    by_family: dict[int, list] = {}
    for p in profiles:
        by_family.setdefault(p.job_family_id, []).append(p)
    for members in by_family.values():
        ranked = sorted(
            ((ladder_rank(p.job_title), p) for p in members if ladder_rank(p.job_title) >= 0),
            key=lambda x: x[0],
        )
        for idx in range(len(ranked) - 1):
            rank_a, prof_a = ranked[idx]
            # link to the nearest higher rank
            for rank_b, prof_b in ranked[idx + 1 :]:
                if rank_b > rank_a:
                    db.add(
                        models.CareerPath(
                            from_profile_id=prof_a.id,
                            to_profile_id=prof_b.id,
                            path_type="next",
                            promotion_criteria="Meets performance standards; demonstrates required competencies at target level",
                            readiness_level="Ready in 1-2 years",
                        )
                    )
                    break
