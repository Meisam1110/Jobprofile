"""Import (Excel bulk upload) and export (Word/PDF/Excel/JSON) endpoints."""
from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .. import models
from ..config import DATA_DIR
from ..database import get_db
from ..security import CurrentUser, require_role
from ..services import exporter
from ..services.importer import import_workbook
from ..services.similarity import INDEX
from ..services.versioning import audit
from .profiles import load_profile

router = APIRouter(prefix="/api", tags=["import-export"])

MEDIA_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "json": "application/json",
}


def _download(content: bytes, filename: str, fmt: str) -> Response:
    return Response(
        content=content,
        media_type=MEDIA_TYPES[fmt],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/profiles/{profile_id}/export")
def export_profile(profile_id: int, fmt: str = Query("pdf", pattern="^(pdf|docx|json)$"), db: Session = Depends(get_db)):
    profile = load_profile(db, profile_id)
    safe_title = "".join(ch for ch in profile.job_title if ch.isalnum() or ch in " -_")[:80].strip()
    if fmt == "pdf":
        return _download(exporter.to_pdf(profile), f"{safe_title}.pdf", "pdf")
    if fmt == "docx":
        return _download(exporter.to_docx(profile), f"{safe_title}.docx", "docx")
    return _download(exporter.to_json(profile), f"{safe_title}.json", "json")


@router.get("/export/excel")
def export_excel(
    db: Session = Depends(get_db),
    status: str = "",
    division: str = "",
    limit: int = Query(2000, le=20000),
):
    query = db.query(models.JobProfile).filter(models.JobProfile.is_active.is_(True))
    if status:
        query = query.filter(models.JobProfile.status == status)
    if division:
        query = query.join(models.OrgUnit, models.JobProfile.division_id == models.OrgUnit.id).filter(models.OrgUnit.name == division)
    profiles = query.order_by(models.JobProfile.job_title).limit(limit).all()
    return _download(exporter.profiles_to_xlsx(profiles), "job_profiles_export.xlsx", "xlsx")


@router.get("/import/template")
def import_template():
    """Blank Excel bulk-upload template with an example row."""
    return _download(exporter.import_template_xlsx(), "job_profile_import_template.xlsx", "xlsx")


@router.post("/import/excel")
async def import_excel(
    file: UploadFile,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role("hr")),
    limit: int | None = None,
):
    """Bulk import from the master workbook format (Job_Profile_Data sheet)."""
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(400, "Upload an .xlsx or .xlsm workbook")
    with tempfile.NamedTemporaryFile(suffix=Path(file.filename).suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        stats = import_workbook(db, tmp_path, limit=limit)
    except KeyError as exc:
        raise HTTPException(400, f"Workbook missing expected sheet: {exc}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    INDEX.dirty = True
    audit(db, user.username, "import_excel", detail=stats)
    db.commit()
    return stats


@router.post("/import/master")
def import_master(db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("hr")), limit: int | None = None):
    """One-click import of the bundled Irancell master workbook (data/)."""
    path = DATA_DIR / "job_profiles_master.xlsm"
    if not path.exists():
        raise HTTPException(404, f"Master workbook not found at {path}")
    stats = import_workbook(db, str(path), limit=limit)
    INDEX.dirty = True
    audit(db, user.username, "import_master", detail=stats)
    db.commit()
    return stats
