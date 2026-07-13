"""Smoke tests over an in-memory database with a small seeded corpus."""
import os
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
_TEST_DB = Path(tempfile.gettempdir()) / "jpms_test.db"
_TEST_DB.unlink(missing_ok=True)
os.environ["JPMS_DATABASE_URL"] = f"sqlite:///{_TEST_DB}"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.services.importer import ensure_grades

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    ensure_grades(db)
    db.commit()
    db.close()


def hr_headers():
    token = client.post("/api/auth/login", json={"username": "hr", "password": "demo"}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_health():
    assert client.get("/api/health").json()["status"] == "ok"


def test_login_and_rbac():
    assert client.post("/api/auth/login", json={"username": "hr", "password": "wrong"}).status_code == 401
    # employees cannot create profiles
    r = client.post("/api/profiles", json={"job_title": "X"})
    assert r.status_code == 403


def test_profile_lifecycle():
    headers = hr_headers()
    payload = {
        "job_title": "Test Planning Senior Specialist",
        "grade_code": "3",
        "division": "Network Group",
        "mission": "Plan and optimize the test network.",
        "responsibilities": [{"text": "Do planning", "pct_time": 60}, {"text": "Do optimization", "pct_time": 40}],
        "kpis": [{"name": "Network availability", "kpi_type": "Individual", "weight": 50}],
        "competencies": [{"name": "Network Planning and Design", "comp_type": "Technical", "required_level": "Advanced"}],
        "skills": [{"name": "Python", "requirement": "preferred", "level": 3}],
        "qualifications": [{"qual_type": "education", "text": "BSc in Telecommunication"}],
    }
    r = client.post("/api/profiles", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    assert r.json()["grade"]["code"] == "3"
    assert len(r.json()["responsibilities"]) == 2

    # update bumps version
    r2 = client.put(f"/api/profiles/{pid}", json={"mission": "Updated mission", "change_note": "edit"}, headers=headers)
    assert r2.json()["mission"] == "Updated mission"
    versions = client.get(f"/api/profiles/{pid}/versions").json()
    assert versions[0]["version_no"] == 2

    # workflow to Published
    for action in ["submit", "approve", "approve", "approve", "approve", "approve", "publish"]:
        r3 = client.post(f"/api/profiles/{pid}/workflow", json={"action": action}, headers=headers)
        assert r3.status_code == 200, f"{action}: {r3.text}"
    assert r3.json()["status"] == "Published"

    # invalid transition rejected
    r4 = client.post(f"/api/profiles/{pid}/workflow", json={"action": "submit"}, headers=headers)
    assert r4.status_code == 400

    # exports
    for fmt, content_type in [("json", "application/json"), ("docx", "application/vnd"), ("pdf", "application/pdf")]:
        r5 = client.get(f"/api/profiles/{pid}/export?fmt={fmt}")
        assert r5.status_code == 200
        assert r5.headers["content-type"].startswith(content_type)

    # search finds it
    hits = client.get("/api/search?q=Test Planning").json()
    assert any(h["id"] == pid for h in hits)

    # compare with itself (duplicate) works
    dup = client.post(f"/api/profiles/{pid}/duplicate", headers=headers)
    assert dup.status_code == 201
    cmp_r = client.get(f"/api/compare?a={pid}&b={dup.json()['id']}")
    assert cmp_r.status_code == 200
    assert cmp_r.json()["fields"]["job_title"]["different"] is True


def test_ai_heuristic():
    r = client.post("/api/ai", json={"task": "estimate_grade", "job_title": "Test Planning Specialist"})
    assert r.status_code == 200
    assert r.json()["provider"] in ("heuristic", "anthropic")
    r2 = client.post("/api/ai", json={"task": "recommend_competencies", "job_title": "Test Planning Specialist"})
    assert isinstance(r2.json()["result"], list)


def test_dashboard():
    data = client.get("/api/analytics/dashboard").json()
    assert data["total_profiles"] >= 1
    assert "by_grade" in data and "by_division" in data
