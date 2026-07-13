"""Job profile CRUD, versions, career paths, workflow actions."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db
from ..security import CurrentUser, get_current_user, require_role
from ..services import workflow as wf
from ..services.importer import get_or_create
from ..services.similarity import INDEX
from ..services.versioning import audit, notify, snapshot

router = APIRouter(prefix="/api/profiles", tags=["profiles"])

DETAIL_OPTIONS = [
    joinedload(models.JobProfile.grade),
    joinedload(models.JobProfile.role_family),
    joinedload(models.JobProfile.job_family),
    joinedload(models.JobProfile.division),
    joinedload(models.JobProfile.department),
]


def load_profile(db: Session, profile_id: int) -> models.JobProfile:
    profile = (
        db.query(models.JobProfile)
        .options(
            *DETAIL_OPTIONS,
            joinedload(models.JobProfile.responsibilities),
            joinedload(models.JobProfile.kpis),
            joinedload(models.JobProfile.profile_competencies).joinedload(models.ProfileCompetency.competency),
            joinedload(models.JobProfile.profile_skills).joinedload(models.ProfileSkill.skill),
            joinedload(models.JobProfile.qualifications),
        )
        .get(profile_id)
    )
    if not profile:
        raise HTTPException(404, "Job profile not found")
    return profile


@router.get("", response_model=schemas.PagedProfiles)
def list_profiles(
    db: Session = Depends(get_db),
    q: str = "",
    status: str = "",
    grade: str = "",
    division: str = "",
    department: str = "",
    role_family: str = "",
    job_family: str = "",
    active: bool | None = None,
    sort: str = "job_title",
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
):
    query = db.query(models.JobProfile).options(*DETAIL_OPTIONS)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                models.JobProfile.job_title.ilike(like),
                models.JobProfile.job_code.ilike(like),
                models.JobProfile.mission.ilike(like),
                models.JobProfile.location.ilike(like),
                models.JobProfile.reports_to.ilike(like),
            )
        )
    if status:
        query = query.filter(models.JobProfile.status == status)
    if active is not None:
        query = query.filter(models.JobProfile.is_active.is_(active))
    if grade:
        query = query.join(models.Grade, models.JobProfile.grade_id == models.Grade.id).filter(models.Grade.code == grade)
    if division:
        query = query.join(models.OrgUnit, models.JobProfile.division_id == models.OrgUnit.id).filter(
            models.OrgUnit.name == division
        )
    if department:
        dept = db.query(models.OrgUnit).filter_by(name=department, unit_type="department").first()
        query = query.filter(models.JobProfile.department_id == (dept.id if dept else -1))
    if role_family:
        rf = db.query(models.RoleFamily).filter_by(name=role_family).first()
        query = query.filter(models.JobProfile.role_family_id == (rf.id if rf else -1))
    if job_family:
        jf = db.query(models.JobFamily).filter_by(name=job_family).first()
        query = query.filter(models.JobProfile.job_family_id == (jf.id if jf else -1))

    total = query.count()
    sort_col = {
        "job_title": models.JobProfile.job_title,
        "updated_at": models.JobProfile.updated_at.desc(),
        "status": models.JobProfile.status,
        "grade": models.JobProfile.grade_id,
    }.get(sort, models.JobProfile.job_title)
    items = query.order_by(sort_col).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/{profile_id}", response_model=schemas.ProfileDetail)
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    return load_profile(db, profile_id)


def _resolve_taxonomy(db: Session, payload: schemas.ProfileCreate | schemas.ProfileUpdate, profile: models.JobProfile):
    if payload.grade_code is not None:
        grade = db.query(models.Grade).filter_by(code=payload.grade_code).first()
        profile.grade_id = grade.id if grade else None
        profile.band = grade.band if grade else profile.band
    if payload.role_family is not None:
        profile.role_family_id = get_or_create(db, models.RoleFamily, name=payload.role_family).id if payload.role_family else None
    if payload.job_family is not None:
        profile.job_family_id = (
            get_or_create(db, models.JobFamily, defaults={"role_family_id": profile.role_family_id}, name=payload.job_family).id
            if payload.job_family
            else None
        )
    if payload.division is not None:
        profile.division_id = (
            get_or_create(db, models.OrgUnit, defaults={"code": ""}, name=payload.division, unit_type="division").id
            if payload.division
            else None
        )
    if payload.department is not None:
        profile.department_id = (
            get_or_create(
                db, models.OrgUnit, defaults={"code": "", "parent_id": profile.division_id}, name=payload.department, unit_type="department"
            ).id
            if payload.department
            else None
        )


SCALAR_FIELDS = [
    "job_title", "job_code", "position_code", "sub_family", "band", "org_level", "location",
    "employment_type", "reports_to", "direct_reports", "job_category", "flsa_status", "language",
    "mission", "context", "business_value", "success_definition", "responsibilities_text",
    "collaboration_text", "authorities_text", "education_text", "experience_text", "trainings_text",
    "behavioral_text", "working_conditions", "performance_standards", "collaboration",
    "authority_matrix", "success_profile", "work_conditions", "signoff", "custom_fields",
]


def _apply_children(db: Session, profile: models.JobProfile, payload: schemas.ProfileCreate):
    db.query(models.Responsibility).filter_by(profile_id=profile.id).delete()
    for i, r in enumerate(payload.responsibilities):
        db.add(models.Responsibility(profile_id=profile.id, sort_order=r.sort_order or i, **r.model_dump(exclude={"sort_order"})))
    db.query(models.ProfileKPI).filter_by(profile_id=profile.id).delete()
    for k in payload.kpis:
        db.add(models.ProfileKPI(profile_id=profile.id, **k.model_dump()))
    db.query(models.ProfileCompetency).filter_by(profile_id=profile.id).delete()
    for c in payload.competencies:
        comp = get_or_create(
            db, models.Competency, defaults={"category": c.category}, name=c.name[:250], comp_type=c.comp_type
        )
        db.add(
            models.ProfileCompetency(
                profile_id=profile.id,
                competency_id=comp.id,
                required_level=c.required_level,
                desired_level=c.desired_level,
                importance=c.importance,
                assessment_method=c.assessment_method,
            )
        )
    db.query(models.ProfileSkill).filter_by(profile_id=profile.id).delete()
    for s in payload.skills:
        skill = get_or_create(db, models.Skill, defaults={"category": s.category}, name=s.name[:250])
        db.add(models.ProfileSkill(profile_id=profile.id, skill_id=skill.id, requirement=s.requirement, level=s.level))
    db.query(models.Qualification).filter_by(profile_id=profile.id).delete()
    for qual in payload.qualifications:
        db.add(models.Qualification(profile_id=profile.id, **qual.model_dump()))


@router.post("", response_model=schemas.ProfileDetail, status_code=201)
def create_profile(
    payload: schemas.ProfileCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("hr")),
):
    profile = models.JobProfile(job_title=payload.job_title, created_by=user.username, updated_by=user.username)
    db.add(profile)
    for field in SCALAR_FIELDS:
        setattr(profile, field, getattr(payload, field))
    _resolve_taxonomy(db, payload, profile)
    db.flush()
    _apply_children(db, profile, payload)
    profile.version = 0
    snapshot(db, profile, user.username, payload.change_note or "Created")
    audit(db, user.username, "create", "profile", profile.id, {"title": profile.job_title})
    db.commit()
    INDEX.dirty = True
    return load_profile(db, profile.id)


@router.put("/{profile_id}", response_model=schemas.ProfileDetail)
def update_profile(
    profile_id: int,
    payload: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("hr")),
):
    profile = load_profile(db, profile_id)
    data = payload.model_dump(exclude_unset=True)
    for field in SCALAR_FIELDS:
        if field in data and data[field] is not None:
            setattr(profile, field, data[field])
    _resolve_taxonomy(db, payload, profile)
    if any(k in data for k in ("responsibilities", "kpis", "competencies", "skills", "qualifications")):
        # full child replacement (editor always sends complete lists)
        merged = schemas.ProfileCreate(
            job_title=profile.job_title,
            responsibilities=payload.responsibilities,
            kpis=payload.kpis,
            competencies=payload.competencies,
            skills=payload.skills,
            qualifications=payload.qualifications,
        )
        _apply_children(db, profile, merged)
    profile.updated_by = user.username
    snapshot(db, profile, user.username, payload.change_note or "Updated")
    audit(db, user.username, "update", "profile", profile.id)
    db.commit()
    INDEX.dirty = True
    return load_profile(db, profile_id)


@router.post("/{profile_id}/duplicate", response_model=schemas.ProfileDetail, status_code=201)
def duplicate_profile(profile_id: int, db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("hr"))):
    """Use an existing profile as a template for a new one."""
    source = load_profile(db, profile_id)
    clone = models.JobProfile(job_title=f"{source.job_title} (Copy)", created_by=user.username, status="Draft", version=0)
    for field in SCALAR_FIELDS:
        if field != "job_title":
            setattr(clone, field, getattr(source, field))
    for rel in ("grade_id", "role_family_id", "job_family_id", "division_id", "department_id"):
        setattr(clone, rel, getattr(source, rel))
    clone.source_file = ""
    db.add(clone)
    db.flush()
    for r in source.responsibilities:
        db.add(models.Responsibility(profile_id=clone.id, text=r.text, pct_time=r.pct_time, frequency=r.frequency, sort_order=r.sort_order))
    for pc in source.profile_competencies:
        db.add(models.ProfileCompetency(profile_id=clone.id, competency_id=pc.competency_id, required_level=pc.required_level, desired_level=pc.desired_level, importance=pc.importance, assessment_method=pc.assessment_method))
    for k in source.kpis:
        db.add(models.ProfileKPI(profile_id=clone.id, name=k.name, kpi_type=k.kpi_type, weight=k.weight, owner=k.owner, formula=k.formula, measurement_method=k.measurement_method))
    for qual in source.qualifications:
        db.add(models.Qualification(profile_id=clone.id, qual_type=qual.qual_type, text=qual.text, mandatory=qual.mandatory))
    snapshot(db, clone, user.username, f"Duplicated from #{source.id}")
    audit(db, user.username, "duplicate", "profile", clone.id, {"source": source.id})
    db.commit()
    INDEX.dirty = True
    return load_profile(db, clone.id)


@router.delete("/{profile_id}", status_code=204)
def deactivate_profile(profile_id: int, db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("hr"))):
    """Soft delete — marks inactive (hard deletes are an admin DB operation)."""
    profile = load_profile(db, profile_id)
    profile.is_active = False
    profile.status = "Archived"
    audit(db, user.username, "deactivate", "profile", profile.id)
    db.commit()
    INDEX.dirty = True


# --------------------------------------------------------------- versions
@router.get("/{profile_id}/versions", response_model=list[schemas.VersionOut])
def list_versions(profile_id: int, db: Session = Depends(get_db)):
    load_profile(db, profile_id)
    return db.query(models.ProfileVersion).filter_by(profile_id=profile_id).order_by(models.ProfileVersion.version_no.desc()).all()


@router.get("/{profile_id}/versions/{version_no}")
def get_version(profile_id: int, version_no: int, db: Session = Depends(get_db)):
    version = db.query(models.ProfileVersion).filter_by(profile_id=profile_id, version_no=version_no).first()
    if not version:
        raise HTTPException(404, "Version not found")
    return {"version_no": version.version_no, "change_note": version.change_note, "changed_by": version.changed_by, "created_at": version.created_at, "snapshot": version.snapshot}


# ------------------------------------------------------------ career path
@router.get("/{profile_id}/career-path", response_model=list[schemas.CareerPathEdge])
def career_path(profile_id: int, db: Session = Depends(get_db)):
    load_profile(db, profile_id)
    edges = []
    for edge in db.query(models.CareerPath).filter_by(from_profile_id=profile_id).all():
        target = edge.to_profile
        edges.append(
            schemas.CareerPathEdge(
                id=edge.id, profile_id=target.id, title=target.job_title,
                grade=target.grade.code if target.grade else "", path_type=edge.path_type,
                direction="outgoing", promotion_criteria=edge.promotion_criteria, readiness_level=edge.readiness_level,
            )
        )
    for edge in db.query(models.CareerPath).filter_by(to_profile_id=profile_id).all():
        source = edge.from_profile
        edges.append(
            schemas.CareerPathEdge(
                id=edge.id, profile_id=source.id, title=source.job_title,
                grade=source.grade.code if source.grade else "", path_type=edge.path_type,
                direction="incoming", promotion_criteria=edge.promotion_criteria, readiness_level=edge.readiness_level,
            )
        )
    return edges


@router.post("/{profile_id}/career-path", status_code=201)
def add_career_edge(profile_id: int, payload: schemas.CareerPathIn, db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("hr"))):
    load_profile(db, profile_id)
    load_profile(db, payload.to_profile_id)
    db.add(models.CareerPath(from_profile_id=profile_id, **payload.model_dump()))
    audit(db, user.username, "career_edge", "profile", profile_id, {"to": payload.to_profile_id})
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------- workflow
@router.get("/{profile_id}/workflow", response_model=list[schemas.WorkflowEventOut])
def workflow_history(profile_id: int, db: Session = Depends(get_db)):
    load_profile(db, profile_id)
    return (
        db.query(models.WorkflowEvent)
        .filter_by(profile_id=profile_id)
        .order_by(models.WorkflowEvent.created_at.desc())
        .all()
    )


@router.post("/{profile_id}/workflow", response_model=schemas.ProfileDetail)
def workflow_action(
    profile_id: int,
    payload: schemas.WorkflowAction,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    profile = load_profile(db, profile_id)
    action = payload.action

    if action == "comment":
        db.add(models.WorkflowEvent(profile_id=profile.id, event_type="comment", actor=user.username, actor_role=user.role, comment=payload.comment))
        db.commit()
        return load_profile(db, profile_id)

    from ..security import ROLE_RANK

    if ROLE_RANK.get(user.role, -1) < ROLE_RANK[wf.minimum_role(action)]:
        raise HTTPException(403, f"Action '{action}' requires role '{wf.minimum_role(action)}' or higher")

    target = wf.next_state(action, profile.status)
    if not target:
        raise HTTPException(400, f"Action '{action}' is not allowed from state '{profile.status}'")

    event_type = "signature" if payload.signature else ("change_request" if action == "request_change" else "transition")
    db.add(
        models.WorkflowEvent(
            profile_id=profile.id, event_type=event_type, from_state=profile.status, to_state=target,
            actor=user.username, actor_role=user.role, comment=payload.comment, signature=payload.signature,
        )
    )
    previous = profile.status
    profile.status = target
    if target == "Published":
        from datetime import datetime, timedelta

        profile.approved_date = datetime.utcnow()
        profile.next_review_date = datetime.utcnow() + timedelta(days=365 * 2)
        profile.is_active = True
        snapshot(db, profile, user.username, f"Published ({payload.comment or 'approved'})")
    notify(db, "hr", "workflow_assigned" if action == "submit" else "approval_pending",
           f"'{profile.job_title}' moved {previous} → {target} by {user.username}", profile.id)
    audit(db, user.username, f"workflow:{action}", "profile", profile.id, {"from": previous, "to": target})
    db.commit()
    return load_profile(db, profile_id)
