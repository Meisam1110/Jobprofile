"""Version snapshots and audit logging."""
from __future__ import annotations

from sqlalchemy.orm import Session

from .. import models
from .exporter import profile_to_dict


def snapshot(db: Session, profile: models.JobProfile, actor: str, note: str = ""):
    """Store the current state as a new immutable version."""
    profile.version = (profile.version or 0) + 1
    db.add(
        models.ProfileVersion(
            profile_id=profile.id,
            version_no=profile.version,
            snapshot=profile_to_dict(profile),
            change_note=note,
            changed_by=actor,
        )
    )


def audit(db: Session, actor: str, action: str, entity: str = "", entity_id: str = "", detail: dict | None = None):
    db.add(models.AuditLog(actor=actor, action=action, entity=entity, entity_id=str(entity_id), detail=detail or {}))


def notify(db: Session, username: str, notif_type: str, message: str, profile_id: int | None = None):
    db.add(models.Notification(username=username, notif_type=notif_type, message=message, profile_id=profile_id))
