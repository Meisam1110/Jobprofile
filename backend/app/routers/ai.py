"""AI assistant endpoints (Module 15)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import CurrentUser, get_current_user
from ..services import ai as ai_service
from ..services.similarity import INDEX
from ..services.versioning import audit

router = APIRouter(prefix="/api/ai", tags=["ai"])

TASKS = [
    "generate_profile", "convert_jd", "improve_writing", "recommend_competencies",
    "recommend_kpis", "recommend_responsibilities", "recommend_qualifications",
    "estimate_grade", "suggest_career_path", "suggest_learning", "find_missing_skills",
    "find_similar", "benchmark", "executive_summary", "translate", "chat",
]


@router.get("/tasks")
def list_tasks():
    return {"tasks": TASKS, "generative_provider_configured": ai_service.anthropic_available()}


@router.post("", response_model=schemas.AIResponse)
def run_ai(payload: schemas.AIRequest, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    if payload.task not in TASKS:
        raise HTTPException(400, f"Unknown task. Available: {', '.join(TASKS)}")
    profile = None
    if payload.profile_id:
        profile = db.get(models.JobProfile, payload.profile_id)
        if not profile:
            raise HTTPException(404, "Job profile not found")
    provider, result = ai_service.run_task(
        db,
        payload.task,
        profile=profile,
        job_title=payload.job_title,
        text=payload.text,
        question=payload.question,
        target_language=payload.target_language,
    )
    audit(db, user.username, f"ai:{payload.task}", "profile", payload.profile_id or "")
    db.commit()
    return {"task": payload.task, "provider": provider, "result": result}


@router.get("/similar/{profile_id}")
def similar(profile_id: int, db: Session = Depends(get_db), top: int = 10):
    if not db.get(models.JobProfile, profile_id):
        raise HTTPException(404, "Job profile not found")
    results = []
    for pid, score in INDEX.similar(db, profile_id=profile_id, top=top):
        p = db.get(models.JobProfile, pid)
        results.append({
            "id": pid, "job_title": p.job_title, "grade": p.grade.code if p.grade else "",
            "division": p.division.name if p.division else "", "similarity": score,
        })
    return results
