"""AI assistant service.

Two providers behind one interface:
  * "anthropic"  — when JPMS_ANTHROPIC_API_KEY is set, tasks are answered by
    the Claude API grounded with corpus context (similar profiles).
  * "heuristic"  — offline fallback that mines the imported corpus (similar
    profiles, competency co-occurrence, grade k-NN) so every AI feature
    still returns useful, Irancell-specific output without a key.
"""
from __future__ import annotations

import json
from collections import Counter

import httpx
from sqlalchemy.orm import Session

from .. import models
from ..config import settings
from .similarity import INDEX, estimate_grade


def profile_brief(profile: models.JobProfile, max_len: int = 1800) -> str:
    comps = ", ".join(pc.competency.name for pc in profile.profile_competencies[:25] if pc.competency)
    parts = [
        f"Title: {profile.job_title}",
        f"Grade/Level: {profile.grade.code if profile.grade else profile.org_level}",
        f"Division: {profile.division.name if profile.division else ''}",
        f"Location: {profile.location}",
        f"Reports to: {profile.reports_to}",
        f"Mission: {profile.mission[:400]}",
        f"Responsibilities: {profile.responsibilities_text[:600]}",
        f"Education: {profile.education_text[:200]}",
        f"Experience: {profile.experience_text[:200]}",
        f"Competencies: {comps}",
    ]
    return "\n".join(p for p in parts if p.split(": ", 1)[-1])[:max_len]


def anthropic_available() -> bool:
    return bool(settings.anthropic_api_key)


def call_anthropic(system: str, user: str, max_tokens: int = 1500) -> str:
    response = httpx.post(
        f"{settings.anthropic_base_url}/v1/messages",
        headers={
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": settings.anthropic_model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        },
        timeout=90,
    )
    response.raise_for_status()
    return "".join(block.get("text", "") for block in response.json().get("content", []))


SYSTEM_PROMPT = (
    "You are the AI assistant inside MTN Irancell's Job Profile Management System. "
    "Follow the official Irancell job profile template with sections: Mission, Context, "
    "Roles & Responsibilities, Collaboration (Direct Reports / Matrix Reports / Key Customers / "
    "Key Suppliers), Authorities, Education, Experience, Technical Competencies "
    "(General Business / Functional / Specialized Knowledge at Basic/Intermediate/Advanced/Expert), "
    "Behavioral Competencies (Live Y'ello values: Lead with Care, Collaborate with Agility, "
    "Act with Inclusion, Serve with Respect, Can-do with Integrity), Trainings, General Working "
    "Condition, Performance Standards. Grades use Irancell levels 1, 2, 2H, 3, 3H, 4, 5. "
    "Ground answers in the reference profiles provided; be concise and use the organization's terminology."
)


def _similar_profiles(db: Session, *, profile_id: int | None = None, text: str | None = None, top: int = 5):
    matches = INDEX.similar(db, profile_id=profile_id, text=text, top=top)
    return [(db.get(models.JobProfile, pid), score) for pid, score in matches]


def _mine_competencies(db: Session, neighbors) -> list[dict]:
    counter: Counter = Counter()
    levels: dict[str, Counter] = {}
    for profile, score in neighbors:
        if not profile:
            continue
        for pc in profile.profile_competencies:
            if pc.competency and pc.competency.comp_type == "Technical":
                counter[pc.competency.name] += score
                levels.setdefault(pc.competency.name, Counter())[pc.required_level or "Intermediate"] += 1
    return [
        {
            "name": name,
            "comp_type": "Technical",
            "required_level": levels[name].most_common(1)[0][0],
            "support": round(weight, 2),
        }
        for name, weight in counter.most_common(15)
    ]


BEHAVIORAL_DEFAULT = [
    {"name": v, "comp_type": "Behavioral", "required_level": "Expected"}
    for v in ["Lead with Care", "Collaborate with Agility", "Act with Inclusion", "Serve with Respect", "Can-do with Integrity"]
]


def run_task(db: Session, task: str, *, profile: models.JobProfile | None, job_title: str | None,
             text: str | None, question: str | None, target_language: str | None) -> tuple[str, object]:
    """Dispatch an AI task. Returns (provider, result)."""
    query_text = text or (profile.job_title if profile else "") or (job_title or "")
    neighbors = _similar_profiles(
        db, profile_id=profile.id if profile else None,
        text=None if profile else f"{job_title or ''} {text or ''}", top=6,
    )
    reference = "\n\n---\n".join(profile_brief(p, 900) for p, _ in neighbors if p)

    if anthropic_available():
        try:
            return "anthropic", _run_anthropic(task, profile, job_title, text, question, target_language, reference)
        except Exception:
            pass  # fall through to the offline engine

    return "heuristic", _run_heuristic(db, task, profile, job_title, text, question, neighbors)


def _run_anthropic(task, profile, job_title, text, question, target_language, reference):
    briefs = f"Reference profiles from the Irancell corpus:\n{reference}\n\n" if reference else ""
    subject = profile_brief(profile) if profile else (text or job_title or "")
    prompts = {
        "generate_profile": f"{briefs}Draft a complete job profile (all template sections) for: {job_title or text}. Return JSON with keys mission, context, responsibilities (array), collaboration, authorities, education, experience, technical_competencies (array of {{name, category, required_level}}), behavioral_competencies (array), trainings, working_conditions, performance_standards, suggested_grade.",
        "convert_jd": f"{briefs}Convert this existing job description into the Irancell template (same JSON keys as a generated profile):\n{text}",
        "improve_writing": f"Improve the writing of this job-profile text: clear, active voice, professional HR tone, keep meaning:\n{text or subject}",
        "recommend_competencies": f"{briefs}Recommend technical and behavioral competencies for:\n{subject}\nReturn JSON array of {{name, comp_type, category, required_level, importance}}.",
        "recommend_kpis": f"{briefs}Recommend 6-10 KPIs for:\n{subject}\nReturn JSON array of {{name, kpi_type, weight, measurement_method}}.",
        "recommend_responsibilities": f"{briefs}Recommend 8-12 responsibility statements for:\n{subject}\nReturn JSON array of strings.",
        "recommend_qualifications": f"{briefs}Recommend qualifications (education, experience, certifications, languages, software) for:\n{subject}\nReturn JSON array of {{qual_type, text, mandatory}}.",
        "estimate_grade": f"{briefs}Estimate the Irancell grade (1,2,2H,3,3H,4,5) for:\n{subject}\nReturn JSON {{grade, rationale}}.",
        "suggest_career_path": f"{briefs}Suggest previous roles, next roles and lateral moves for:\n{subject}\nReturn JSON {{previous: [], next: [], lateral: []}}.",
        "suggest_learning": f"{briefs}Suggest mandatory courses, recommended courses and certifications for:\n{subject}\nReturn JSON {{mandatory: [], recommended: [], certifications: []}}.",
        "find_missing_skills": f"{briefs}What skills/competencies are missing or under-specified in this profile compared to similar roles?\n{subject}\nReturn JSON array of {{name, reason}}.",
        "executive_summary": f"Write a 5-sentence executive summary of this job profile:\n{subject}",
        "translate": f"Translate this job profile content to {target_language or 'Persian (Farsi)'}, keeping section headings:\n{subject}",
        "benchmark": f"{briefs}Benchmark this profile against the internal reference profiles and telecom-industry norms. Cover scope, grade alignment, competency coverage and gaps:\n{subject}",
        "chat": f"{briefs}Job profile under discussion:\n{subject}\n\nQuestion: {question}",
    }
    prompt = prompts.get(task) or prompts["chat"]
    raw = call_anthropic(SYSTEM_PROMPT, prompt)
    # Return parsed JSON when the task requested it
    stripped = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    if stripped[:1] in "[{":
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
    return raw


def _run_heuristic(db: Session, task, profile, job_title, text, question, neighbors):
    title = (profile.job_title if profile else None) or job_title or "Untitled role"
    top = [{"id": p.id, "title": p.job_title, "grade": p.grade.code if p.grade else "", "similarity": s}
           for p, s in neighbors if p]

    if task in {"recommend_competencies", "find_missing_skills"}:
        mined = _mine_competencies(db, neighbors)
        if task == "find_missing_skills" and profile:
            have = {pc.competency.name.lower() for pc in profile.profile_competencies if pc.competency}
            mined = [m for m in mined if m["name"].lower() not in have]
            return [{"name": m["name"], "reason": f"Present in similar roles (support {m['support']})"} for m in mined[:10]]
        return mined + BEHAVIORAL_DEFAULT

    if task == "estimate_grade":
        return estimate_grade(db, title, text or "")

    if task in {"generate_profile", "convert_jd"}:
        mined = _mine_competencies(db, neighbors)
        best = neighbors[0][0] if neighbors and neighbors[0][0] else None
        grade_est = estimate_grade(db, title, text or "")
        return {
            "note": "Corpus-based draft assembled from the most similar existing Irancell profiles. Configure JPMS_ANTHROPIC_API_KEY for generative drafting.",
            "based_on": top,
            "mission": best.mission if best else "",
            "context": best.context if best else "",
            "responsibilities": [r.text for r in (best.responsibilities if best else [])][:12],
            "education": best.education_text if best else "",
            "experience": best.experience_text if best else "",
            "technical_competencies": mined,
            "behavioral_competencies": [b["name"] for b in BEHAVIORAL_DEFAULT],
            "trainings": best.trainings_text if best else "",
            "working_conditions": best.working_conditions if best else "General MTNIrancell working conditions",
            "performance_standards": best.performance_standards if best else "As per performance agreement",
            "suggested_grade": grade_est.get("grade"),
        }

    if task == "recommend_responsibilities":
        seen, out = set(), []
        for p, _ in neighbors:
            for r in (p.responsibilities if p else [])[:6]:
                key = r.text[:60].lower()
                if key not in seen:
                    seen.add(key)
                    out.append(r.text)
        return out[:12]

    if task == "recommend_kpis":
        return [
            {"name": "Delivery against annual objectives", "kpi_type": "Individual", "weight": 30, "measurement_method": "Performance agreement scoring"},
            {"name": "Quality / accuracy of outputs", "kpi_type": "Individual", "weight": 20, "measurement_method": "Error rate, rework"},
            {"name": "Stakeholder satisfaction", "kpi_type": "Team", "weight": 15, "measurement_method": "Internal NPS survey"},
            {"name": "Process / SLA compliance", "kpi_type": "Department", "weight": 20, "measurement_method": "SLA dashboard"},
            {"name": "Contribution to strategic initiatives", "kpi_type": "Strategic", "weight": 15, "measurement_method": "Initiative milestone completion"},
        ]

    if task == "recommend_qualifications":
        best = neighbors[0][0] if neighbors and neighbors[0][0] else None
        out = []
        if best:
            if best.education_text:
                out.append({"qual_type": "education", "text": best.education_text, "mandatory": True})
            if best.experience_text:
                out.append({"qual_type": "experience", "text": best.experience_text, "mandatory": True})
            if best.trainings_text:
                out.append({"qual_type": "training", "text": best.trainings_text, "mandatory": False})
        out.append({"qual_type": "language", "text": "English literacy — Intermediate or above", "mandatory": True})
        return out

    if task == "suggest_career_path":
        edges_out = db.query(models.CareerPath).filter_by(from_profile_id=profile.id).all() if profile else []
        edges_in = db.query(models.CareerPath).filter_by(to_profile_id=profile.id).all() if profile else []
        return {
            "previous": [{"id": e.from_profile.id, "title": e.from_profile.job_title} for e in edges_in],
            "next": [{"id": e.to_profile.id, "title": e.to_profile.job_title} for e in edges_out],
            "lateral": top[:3],
        }

    if task == "suggest_learning":
        best = neighbors[0][0] if neighbors and neighbors[0][0] else None
        return {
            "mandatory": [t.strip() for t in (profile.trainings_text if profile else (best.trainings_text if best else "")).split("\n") if t.strip()][:6],
            "recommended": ["MTN Irancell Products & Services Introduction", "Data literacy fundamentals"],
            "certifications": [],
        }

    if task == "find_similar" or task == "benchmark":
        return {"similar_profiles": top, "note": "Similarity by TF-IDF over title, mission, responsibilities and competencies."}

    if task == "executive_summary":
        if not profile:
            return f"No stored profile selected; most similar existing roles: {', '.join(t['title'] for t in top[:3])}."
        grade = profile.grade.code if profile.grade else profile.org_level
        comp_count = len(profile.profile_competencies)
        return (
            f"{profile.job_title} is a level-{grade} role in {profile.division.name if profile.division else 'the organization'} "
            f"({profile.location}), reporting to {profile.reports_to or 'N/A'} with {profile.direct_reports} direct subordinates. "
            f"Mission: {profile.mission[:220]}. The profile defines {len(profile.responsibilities)} responsibilities and "
            f"{comp_count} competencies, with performance measured by: {profile.performance_standards[:120] or 'the annual performance agreement'}. "
            f"Current workflow status: {profile.status} (v{profile.version})."
        )

    if task == "improve_writing":
        return {"note": "Generative rewriting requires JPMS_ANTHROPIC_API_KEY.", "original": text}

    if task == "translate":
        return {"note": "Translation requires JPMS_ANTHROPIC_API_KEY.", "original": text}

    # chat fallback: keyword answers grounded in the profile
    if profile and question:
        q = question.lower()
        if "competenc" in q:
            return [f"{pc.competency.name} — {pc.required_level}" for pc in profile.profile_competencies if pc.competency]
        if "career" in q or "path" in q or "next" in q:
            return _run_heuristic(db, "suggest_career_path", profile, None, None, None, neighbors)
        if "kpi" in q or "performance" in q:
            return profile.performance_standards or "As per performance agreement"
        if "report" in q:
            return {"reports_to": profile.reports_to, "direct_reports": profile.direct_reports, "collaboration": profile.collaboration}
        if "grade" in q or "level" in q:
            return {"grade": profile.grade.code if profile.grade else profile.org_level, "band": profile.band}
        if "similar" in q or "match" in q:
            return top
        return profile_brief(profile)
    return {"similar_profiles": top}
