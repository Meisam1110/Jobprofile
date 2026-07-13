"""Auth, taxonomy lookups, search, analytics, comparison, notifications, admin."""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import DEMO_PASSWORD, DEMO_USERS, CurrentUser, get_current_user, make_token, require_role
from ..services.similarity import INDEX, find_duplicates
from ..services.versioning import audit

router = APIRouter(prefix="/api", tags=["core"])


# -------------------------------------------------------------------- auth
@router.post("/auth/login", response_model=schemas.LoginResponse)
def login(payload: schemas.LoginRequest):
    user = DEMO_USERS.get(payload.username)
    if not user or payload.password != DEMO_PASSWORD:
        raise HTTPException(401, "Invalid credentials (demo users: admin/hr/manager/employee, password 'demo')")
    return {
        "token": make_token(payload.username, user["role"]),
        "username": payload.username,
        "full_name": user["full_name"],
        "role": user["role"],
    }


@router.get("/auth/me")
def me(user: CurrentUser = Depends(get_current_user)):
    return {"username": user.username, "role": user.role}


# ---------------------------------------------------------------- taxonomy
@router.get("/taxonomy")
def taxonomy(db: Session = Depends(get_db)):
    """All filter dimensions in one call (drives the UI facets)."""
    return {
        "grades": [schemas.GradeOut.model_validate(g) for g in db.query(models.Grade).order_by(models.Grade.rank)],
        "divisions": [
            schemas.OrgUnitOut.model_validate(o)
            for o in db.query(models.OrgUnit).filter_by(unit_type="division").order_by(models.OrgUnit.name)
        ],
        "role_families": [schemas.RoleFamilyOut.model_validate(r) for r in db.query(models.RoleFamily).order_by(models.RoleFamily.name)],
        "job_families": [schemas.JobFamilyOut.model_validate(j) for j in db.query(models.JobFamily).order_by(models.JobFamily.name)],
        "statuses": ["Draft", "Under Review", "HR Review", "Business Review", "Organization Design Review", "Compensation Review", "Executive Approval", "Published", "Archived"],
        "competency_types": ["Technical", "Behavioral", "Leadership", "Digital", "AI", "Future"],
        "competency_levels": ["Basic", "Intermediate", "Advanced", "Expert"],
    }


@router.get("/competencies", response_model=list[schemas.CompetencyOut])
def list_competencies(db: Session = Depends(get_db), q: str = "", comp_type: str = "", limit: int = Query(50, le=500)):
    query = db.query(models.Competency)
    if q:
        query = query.filter(models.Competency.name.ilike(f"%{q}%"))
    if comp_type:
        query = query.filter(models.Competency.comp_type == comp_type)
    return query.order_by(models.Competency.name).limit(limit).all()


# ------------------------------------------------------------------ search
@router.get("/search")
def search(
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=1),
    limit: int = Query(20, le=100),
    semantic: bool = False,
):
    """Full-text search over titles + all template sections, with optional
    semantic (TF-IDF) ranking for natural-language queries."""
    like = f"%{q}%"
    base = db.query(models.JobProfile).filter(models.JobProfile.is_active.is_(True))
    text_hits = (
        base.filter(
            or_(
                models.JobProfile.job_title.ilike(like),
                models.JobProfile.job_code.ilike(like),
                models.JobProfile.mission.ilike(like),
                models.JobProfile.context.ilike(like),
                models.JobProfile.responsibilities_text.ilike(like),
                models.JobProfile.education_text.ilike(like),
                models.JobProfile.experience_text.ilike(like),
                models.JobProfile.location.ilike(like),
                models.JobProfile.reports_to.ilike(like),
            )
        )
        .limit(limit)
        .all()
    )
    results = [
        {"id": p.id, "job_title": p.job_title, "location": p.location, "status": p.status,
         "grade": p.grade.code if p.grade else "", "match": "text"}
        for p in text_hits
    ]
    # competency-name hits
    comp_hits = (
        db.query(models.JobProfile)
        .join(models.ProfileCompetency, models.ProfileCompetency.profile_id == models.JobProfile.id)
        .join(models.Competency, models.Competency.id == models.ProfileCompetency.competency_id)
        .filter(models.Competency.name.ilike(like), models.JobProfile.is_active.is_(True))
        .limit(limit)
        .all()
    )
    seen = {r["id"] for r in results}
    for p in comp_hits:
        if p.id not in seen:
            seen.add(p.id)
            results.append({"id": p.id, "job_title": p.job_title, "location": p.location, "status": p.status,
                            "grade": p.grade.code if p.grade else "", "match": "competency"})
    if semantic or len(results) < 5:
        for pid, score in INDEX.similar(db, text=q, top=limit):
            if pid not in seen:
                seen.add(pid)
                profile = db.get(models.JobProfile, pid)
                results.append({"id": pid, "job_title": profile.job_title, "location": profile.location,
                                "status": profile.status, "grade": profile.grade.code if profile.grade else "",
                                "match": f"semantic ({score})"})
    return results[:limit]


@router.get("/search/autocomplete")
def autocomplete(db: Session = Depends(get_db), q: str = Query(..., min_length=1)):
    titles = (
        db.query(models.JobProfile.id, models.JobProfile.job_title)
        .filter(models.JobProfile.job_title.ilike(f"%{q}%"), models.JobProfile.is_active.is_(True))
        .order_by(models.JobProfile.job_title)
        .limit(10)
        .all()
    )
    return [{"id": i, "job_title": t} for i, t in titles]


# --------------------------------------------------------------- analytics
@router.get("/analytics/dashboard")
def dashboard(db: Session = Depends(get_db)):
    total = db.query(func.count(models.JobProfile.id)).scalar()
    active = db.query(func.count(models.JobProfile.id)).filter(models.JobProfile.is_active.is_(True)).scalar()

    by_status = dict(db.query(models.JobProfile.status, func.count()).group_by(models.JobProfile.status).all())
    by_grade = dict(
        db.query(models.Grade.code, func.count())
        .join(models.JobProfile, models.JobProfile.grade_id == models.Grade.id)
        .group_by(models.Grade.code)
        .all()
    )
    by_division = (
        db.query(models.OrgUnit.name, func.count())
        .join(models.JobProfile, models.JobProfile.division_id == models.OrgUnit.id)
        .group_by(models.OrgUnit.name)
        .order_by(func.count().desc())
        .all()
    )
    by_family = (
        db.query(models.JobFamily.name, func.count())
        .join(models.JobProfile, models.JobProfile.job_family_id == models.JobFamily.id)
        .group_by(models.JobFamily.name)
        .order_by(func.count().desc())
        .limit(15)
        .all()
    )
    two_years_ago = datetime.utcnow() - timedelta(days=730)
    outdated = (
        db.query(func.count(models.JobProfile.id))
        .filter(models.JobProfile.approved_date.isnot(None), models.JobProfile.approved_date < two_years_ago)
        .scalar()
    )
    awaiting = (
        db.query(func.count(models.JobProfile.id))
        .filter(models.JobProfile.status.notin_(["Draft", "Published", "Archived"]))
        .scalar()
    )
    avg_age_days = db.query(
        func.avg(func.julianday(datetime.utcnow()) - func.julianday(models.JobProfile.approved_date))
    ).filter(models.JobProfile.approved_date.isnot(None)).scalar() if db.bind.dialect.name == "sqlite" else None

    career_covered = db.query(func.count(func.distinct(models.CareerPath.from_profile_id))).scalar()
    competency_dist = dict(
        db.query(models.Competency.comp_type, func.count())
        .join(models.ProfileCompetency, models.ProfileCompetency.competency_id == models.Competency.id)
        .group_by(models.Competency.comp_type)
        .all()
    )
    top_competencies = (
        db.query(models.Competency.name, func.count())
        .join(models.ProfileCompetency, models.ProfileCompetency.competency_id == models.Competency.id)
        .filter(models.Competency.comp_type == "Technical")
        .group_by(models.Competency.name)
        .order_by(func.count().desc())
        .limit(15)
        .all()
    )
    missing_grade = db.query(func.count(models.JobProfile.id)).filter(models.JobProfile.grade_id.is_(None)).scalar()

    return {
        "total_profiles": total,
        "active_profiles": active,
        "by_status": by_status,
        "by_grade": by_grade,
        "by_division": [{"name": n, "count": c} for n, c in by_division],
        "by_job_family": [{"name": n, "count": c} for n, c in by_family],
        "competency_distribution": competency_dist,
        "top_competencies": [{"name": n, "count": c} for n, c in top_competencies],
        "outdated_profiles": outdated,
        "awaiting_approval": awaiting,
        "avg_review_age_days": round(avg_age_days) if avg_age_days else None,
        "career_path_coverage": round((career_covered / active) * 100, 1) if active else 0,
        "profiles_missing_grade": missing_grade,
    }


@router.get("/analytics/duplicates")
def duplicates(db: Session = Depends(get_db), threshold: float = Query(0.82, ge=0.5, le=1.0)):
    return find_duplicates(db, threshold=threshold)


@router.get("/analytics/heatmap")
def heatmap(db: Session = Depends(get_db)):
    """Job family x grade counts for the coverage heat map."""
    rows = (
        db.query(models.JobFamily.name, models.Grade.code, func.count())
        .join(models.JobProfile, models.JobProfile.job_family_id == models.JobFamily.id)
        .join(models.Grade, models.JobProfile.grade_id == models.Grade.id)
        .group_by(models.JobFamily.name, models.Grade.code)
        .all()
    )
    top_families = {}
    for family, grade, count in rows:
        top_families.setdefault(family, {"family": family, "total": 0})
        top_families[family][grade] = count
        top_families[family]["total"] += count
    ranked = sorted(top_families.values(), key=lambda x: -x["total"])[:25]
    return {"grades": ["1", "2", "2H", "3", "3H", "4", "5"], "rows": ranked}


# --------------------------------------------------------------- comparison
COMPARE_FIELDS = [
    "job_title", "location", "reports_to", "direct_reports", "mission", "context",
    "authorities_text", "education_text", "experience_text", "trainings_text",
    "working_conditions", "performance_standards", "status",
]


@router.get("/compare")
def compare(a: int, b: int, db: Session = Depends(get_db)):
    pa, pb = db.get(models.JobProfile, a), db.get(models.JobProfile, b)
    if not pa or not pb:
        raise HTTPException(404, "One or both profiles not found")

    def comp_map(p):
        return {
            pc.competency.name: pc.required_level
            for pc in p.profile_competencies
            if pc.competency and pc.competency.comp_type == "Technical"
        }

    ca, cb = comp_map(pa), comp_map(pb)
    fields = {}
    for field in COMPARE_FIELDS:
        va, vb = getattr(pa, field), getattr(pb, field)
        fields[field] = {"a": va, "b": vb, "different": str(va).strip() != str(vb).strip()}
    fields["grade"] = {
        "a": pa.grade.code if pa.grade else "",
        "b": pb.grade.code if pb.grade else "",
        "different": (pa.grade.code if pa.grade else "") != (pb.grade.code if pb.grade else ""),
    }
    return {
        "a": {"id": pa.id, "job_title": pa.job_title},
        "b": {"id": pb.id, "job_title": pb.job_title},
        "fields": fields,
        "competencies": {
            "only_a": sorted(set(ca) - set(cb)),
            "only_b": sorted(set(cb) - set(ca)),
            "shared": [{"name": n, "a_level": ca[n], "b_level": cb[n], "different": ca[n] != cb[n]} for n in sorted(set(ca) & set(cb))],
        },
        "responsibilities": {
            "a": [r.text for r in pa.responsibilities],
            "b": [r.text for r in pb.responsibilities],
        },
        "kpis": {
            "a": [k.name for k in pa.kpis],
            "b": [k.name for k in pb.kpis],
        },
        "qualifications": {
            "a": [{"type": q.qual_type, "text": q.text} for q in pa.qualifications],
            "b": [{"type": q.qual_type, "text": q.text} for q in pb.qualifications],
        },
    }


# ------------------------------------------------------------ notifications
@router.get("/notifications", response_model=list[schemas.NotificationOut])
def notifications(db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    return (
        db.query(models.Notification)
        .filter(or_(models.Notification.username == user.username, models.Notification.username == user.role))
        .order_by(models.Notification.created_at.desc())
        .limit(50)
        .all()
    )


@router.post("/notifications/{notif_id}/read")
def mark_read(notif_id: int, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    notif = db.get(models.Notification, notif_id)
    if notif:
        notif.is_read = True
        db.commit()
    return {"ok": True}


# ------------------------------------------------------------------- admin
@router.get("/admin/audit")
def audit_logs(db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("admin")), limit: int = Query(100, le=1000)):
    logs = db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(limit).all()
    return [
        {"id": l.id, "actor": l.actor, "action": l.action, "entity": l.entity, "entity_id": l.entity_id,
         "detail": l.detail, "created_at": l.created_at}
        for l in logs
    ]


@router.post("/admin/review-scan")
def review_scan(db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("hr"))):
    """Generate review-due / expired notifications (run periodically)."""
    from ..services.versioning import notify

    now = datetime.utcnow()
    due = (
        db.query(models.JobProfile)
        .filter(models.JobProfile.next_review_date.isnot(None), models.JobProfile.next_review_date < now)
        .all()
    )
    stale = (
        db.query(models.JobProfile)
        .filter(models.JobProfile.approved_date.isnot(None), models.JobProfile.approved_date < now - timedelta(days=730))
        .limit(500)
        .all()
    )
    for p in due:
        notify(db, "hr", "review_due", f"Review due for '{p.job_title}'", p.id)
    for p in stale[:50]:
        notify(db, "hr", "profile_expired", f"'{p.job_title}' has not been reviewed for over 2 years", p.id)
    audit(db, user.username, "review_scan", detail={"due": len(due), "stale": len(stale)})
    db.commit()
    return {"review_due": len(due), "expired": len(stale)}
