"""Irancell Enterprise Job Profile Management System — API entry point.

Run:  uvicorn app.main:app --reload   (from backend/)
Docs: http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import settings
from .database import Base, engine
from .routers import ai, importexport, misc, profiles

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Single source of truth for every job profile at MTN Irancell — "
        "job architecture, competencies, workflow, analytics and AI assistance."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(misc.router)
app.include_router(profiles.router)
app.include_router(ai.router)
app.include_router(importexport.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}


# Serve the built frontend when present (single-container deployment).
_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")
