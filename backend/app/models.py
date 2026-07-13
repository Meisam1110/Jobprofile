"""Normalized data model for the Job Profile master record.

Entity map (see docs/09-database-design.md for the ER diagram):
  OrgUnit ─┬─ JobProfile ─┬─ Responsibility
  RoleFamily┤             ├─ ProfileKPI
  JobFamily ┤             ├─ ProfileCompetency ── Competency
  Grade ────┘             ├─ ProfileSkill ─────── Skill
                          ├─ Qualification
                          ├─ CareerPath (from/to)
                          ├─ ProfileVersion
                          ├─ WorkflowEvent
                          ├─ Attachment
                          └─ AuditLog / Notification
  Employee / Position link profiles into the wider org.
"""
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.utcnow()


# ---------------------------------------------------------------- taxonomy
class OrgUnit(Base):
    """Division / department hierarchy (e.g. NWG -> Transmission Planning)."""

    __tablename__ = "org_units"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    code: Mapped[str] = mapped_column(String(32), index=True, default="")
    unit_type: Mapped[str] = mapped_column(String(32), default="department")  # division|department|unit
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("org_units.id"), nullable=True)
    parent = relationship("OrgUnit", remote_side=[id], backref="children")
    __table_args__ = (UniqueConstraint("name", "unit_type", name="uq_orgunit_name_type"),)


class RoleFamily(Base):
    __tablename__ = "role_families"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")


class JobFamily(Base):
    __tablename__ = "job_families"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    role_family_id: Mapped[int | None] = mapped_column(ForeignKey("role_families.id"), nullable=True)
    role_family = relationship("RoleFamily", backref="job_families")


class Grade(Base):
    """Irancell level structure: 1, 2, 2H, 3, 3H, 4, 5."""

    __tablename__ = "grades"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True)  # e.g. "3H"
    rank: Mapped[int] = mapped_column(Integer, default=0)  # sortable ordinal
    band: Mapped[str] = mapped_column(String(64), default="")
    description: Mapped[str] = mapped_column(Text, default="")


class Competency(Base):
    __tablename__ = "competencies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    # Technical | Behavioral | Leadership | Digital | AI | Future
    comp_type: Mapped[str] = mapped_column(String(32), default="Technical", index=True)
    # Irancell knowledge categories: General Business / Functional / Specialized Knowledge
    category: Mapped[str] = mapped_column(String(64), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    __table_args__ = (UniqueConstraint("name", "comp_type", name="uq_comp_name_type"),)


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(64), default="")


# ------------------------------------------------------------- job profile
class JobProfile(Base):
    __tablename__ = "job_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)

    # Module 2 — Job Information (Irancell template header block)
    job_title: Mapped[str] = mapped_column(String(255), index=True)
    job_code: Mapped[str] = mapped_column(String(64), default="", index=True)
    position_code: Mapped[str] = mapped_column(String(64), default="")
    sub_family: Mapped[str] = mapped_column(String(255), default="")
    band: Mapped[str] = mapped_column(String(64), default="")
    org_level: Mapped[str] = mapped_column(String(64), default="")
    location: Mapped[str] = mapped_column(String(255), default="")  # "Location of the Job"
    employment_type: Mapped[str] = mapped_column(String(64), default="Full-time")
    reports_to: Mapped[str] = mapped_column(String(255), default="")
    direct_reports: Mapped[int] = mapped_column(Integer, default=0)  # "Number of subordinates"
    job_category: Mapped[str] = mapped_column(String(128), default="")
    flsa_status: Mapped[str] = mapped_column(String(64), default="")
    language: Mapped[str] = mapped_column(String(16), default="en")

    role_family_id: Mapped[int | None] = mapped_column(ForeignKey("role_families.id"), nullable=True)
    job_family_id: Mapped[int | None] = mapped_column(ForeignKey("job_families.id"), nullable=True)
    grade_id: Mapped[int | None] = mapped_column(ForeignKey("grades.id"), nullable=True)
    division_id: Mapped[int | None] = mapped_column(ForeignKey("org_units.id"), nullable=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("org_units.id"), nullable=True)

    # Module 3 — Job Purpose (template: Mission / Context)
    mission: Mapped[str] = mapped_column(Text, default="")
    context: Mapped[str] = mapped_column(Text, default="")
    business_value: Mapped[str] = mapped_column(Text, default="")
    success_definition: Mapped[str] = mapped_column(Text, default="")

    # Template long-text sections kept verbatim for fidelity
    responsibilities_text: Mapped[str] = mapped_column(Text, default="")  # Roles & Responsibilities
    collaboration_text: Mapped[str] = mapped_column(Text, default="")  # Collaboration
    authorities_text: Mapped[str] = mapped_column(Text, default="")  # Authorities
    education_text: Mapped[str] = mapped_column(Text, default="")  # Education
    experience_text: Mapped[str] = mapped_column(Text, default="")  # Experience
    trainings_text: Mapped[str] = mapped_column(Text, default="")  # Trainings
    behavioral_text: Mapped[str] = mapped_column(Text, default="")  # Behavioral Competencies (verbatim)
    working_conditions: Mapped[str] = mapped_column(Text, default="")  # General Working Condition
    performance_standards: Mapped[str] = mapped_column(Text, default="")  # Performance Standards

    # Module 9 — Organizational Relationships (parsed from Collaboration)
    collaboration: Mapped[dict] = mapped_column(JSON, default=dict)
    # Module 10 — Authority matrix rows [{area, authority, limit}]
    authority_matrix: Mapped[list] = mapped_column(JSON, default=list)
    # Module 12 — Success profile
    success_profile: Mapped[dict] = mapped_column(JSON, default=dict)
    # Module 14 — Work conditions structured {mode, travel, shift, hours, physical, environment}
    work_conditions: Mapped[dict] = mapped_column(JSON, default=dict)
    # Signoff block: {line_manager, functional_manager, oa, hod, chro, ceo_coo}
    signoff: Mapped[dict] = mapped_column(JSON, default=dict)
    # Dynamic metadata / custom fields
    custom_fields: Mapped[dict] = mapped_column(JSON, default=dict)

    # Lifecycle
    status: Mapped[str] = mapped_column(String(32), default="Draft", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    document_version: Mapped[str] = mapped_column(String(32), default="1.0")
    approved_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_review_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source_file: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    created_by: Mapped[str] = mapped_column(String(128), default="system")
    updated_by: Mapped[str] = mapped_column(String(128), default="system")

    role_family = relationship("RoleFamily")
    job_family = relationship("JobFamily")
    grade = relationship("Grade")
    division = relationship("OrgUnit", foreign_keys=[division_id])
    department = relationship("OrgUnit", foreign_keys=[department_id])

    responsibilities = relationship("Responsibility", back_populates="profile", cascade="all, delete-orphan")
    kpis = relationship("ProfileKPI", back_populates="profile", cascade="all, delete-orphan")
    profile_competencies = relationship(
        "ProfileCompetency", back_populates="profile", cascade="all, delete-orphan"
    )
    profile_skills = relationship("ProfileSkill", back_populates="profile", cascade="all, delete-orphan")
    qualifications = relationship("Qualification", back_populates="profile", cascade="all, delete-orphan")
    versions = relationship(
        "ProfileVersion", back_populates="profile", cascade="all, delete-orphan", order_by="ProfileVersion.version_no"
    )
    workflow_events = relationship(
        "WorkflowEvent", back_populates="profile", cascade="all, delete-orphan", order_by="WorkflowEvent.created_at"
    )
    attachments = relationship("Attachment", back_populates="profile", cascade="all, delete-orphan")


class Responsibility(Base):
    """Module 4 — responsibilities with % of time, cadence and authority."""

    __tablename__ = "responsibilities"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("job_profiles.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    pct_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    frequency: Mapped[str] = mapped_column(String(32), default="")  # daily|weekly|monthly|adhoc
    key_tasks: Mapped[str] = mapped_column(Text, default="")
    deliverables: Mapped[str] = mapped_column(Text, default="")
    decision_authority: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    profile = relationship("JobProfile", back_populates="responsibilities")


class ProfileKPI(Base):
    """Module 5 — KPI management."""

    __tablename__ = "profile_kpis"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("job_profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    kpi_type: Mapped[str] = mapped_column(String(32), default="Individual")  # Individual|Team|Department|Strategic
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    owner: Mapped[str] = mapped_column(String(128), default="")
    formula: Mapped[str] = mapped_column(Text, default="")
    measurement_method: Mapped[str] = mapped_column(Text, default="")
    profile = relationship("JobProfile", back_populates="kpis")


class ProfileCompetency(Base):
    """Module 6 — competency requirements per profile."""

    __tablename__ = "profile_competencies"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("job_profiles.id"), index=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id"), index=True)
    required_level: Mapped[str] = mapped_column(String(32), default="")  # Basic|Intermediate|Advance|Expert
    desired_level: Mapped[str] = mapped_column(String(32), default="")
    importance: Mapped[str] = mapped_column(String(32), default="")  # Critical|High|Medium|Low
    assessment_method: Mapped[str] = mapped_column(String(128), default="")
    profile = relationship("JobProfile", back_populates="profile_competencies")
    competency = relationship("Competency")


class ProfileSkill(Base):
    """Module 8 — skills matrix (levels 1–5)."""

    __tablename__ = "profile_skills"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("job_profiles.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    requirement: Mapped[str] = mapped_column(String(16), default="required")  # required|preferred|future
    level: Mapped[int] = mapped_column(Integer, default=3)  # 1..5
    profile = relationship("JobProfile", back_populates="profile_skills")
    skill = relationship("Skill")


class Qualification(Base):
    """Module 7 — education/experience/certifications/languages/etc."""

    __tablename__ = "qualifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("job_profiles.id"), index=True)
    # education|experience|certification|language|software|license|training|preferred
    qual_type: Mapped[str] = mapped_column(String(32), index=True)
    text: Mapped[str] = mapped_column(Text)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    profile = relationship("JobProfile", back_populates="qualifications")


class CareerPath(Base):
    """Module 11 — career ladder/lattice edges between profiles."""

    __tablename__ = "career_paths"
    id: Mapped[int] = mapped_column(primary_key=True)
    from_profile_id: Mapped[int] = mapped_column(ForeignKey("job_profiles.id"), index=True)
    to_profile_id: Mapped[int] = mapped_column(ForeignKey("job_profiles.id"), index=True)
    path_type: Mapped[str] = mapped_column(String(16), default="next")  # next|lateral
    promotion_criteria: Mapped[str] = mapped_column(Text, default="")
    readiness_level: Mapped[str] = mapped_column(String(64), default="")
    from_profile = relationship("JobProfile", foreign_keys=[from_profile_id])
    to_profile = relationship("JobProfile", foreign_keys=[to_profile_id])
    __table_args__ = (UniqueConstraint("from_profile_id", "to_profile_id", "path_type", name="uq_career_edge"),)


class LearningItem(Base):
    """Module 13 — learning & development linked to a profile."""

    __tablename__ = "learning_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("job_profiles.id"), index=True)
    # mandatory_course|recommended_course|certification|learning_path|development_plan|coaching|mentoring
    item_type: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    profile = relationship("JobProfile")


class ProfileVersion(Base):
    __tablename__ = "profile_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("job_profiles.id"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict] = mapped_column(JSON)
    change_note: Mapped[str] = mapped_column(Text, default="")
    changed_by: Mapped[str] = mapped_column(String(128), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    profile = relationship("JobProfile", back_populates="versions")
    __table_args__ = (UniqueConstraint("profile_id", "version_no", name="uq_profile_version"),)


class WorkflowEvent(Base):
    """Approval workflow trail: state transitions, comments, signatures."""

    __tablename__ = "workflow_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("job_profiles.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(32), default="transition")  # transition|comment|change_request|signature
    from_state: Mapped[str] = mapped_column(String(32), default="")
    to_state: Mapped[str] = mapped_column(String(32), default="")
    actor: Mapped[str] = mapped_column(String(128), default="")
    actor_role: Mapped[str] = mapped_column(String(64), default="")
    comment: Mapped[str] = mapped_column(Text, default="")
    signature: Mapped[str] = mapped_column(String(255), default="")  # digital signature hash
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    profile = relationship("JobProfile", back_populates="workflow_events")


class Attachment(Base):
    __tablename__ = "attachments"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("job_profiles.id"), index=True)
    filename: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(128), default="")
    path: Mapped[str] = mapped_column(String(1024))
    uploaded_by: Mapped[str] = mapped_column(String(128), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    profile = relationship("JobProfile", back_populates="attachments")


# ------------------------------------------------------------ organization
class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_no: Mapped[str] = mapped_column(String(32), unique=True)
    full_name: Mapped[str] = mapped_column(String(255), index=True)
    email: Mapped[str] = mapped_column(String(255), default="")
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("job_profiles.id"), nullable=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    skills: Mapped[list] = mapped_column(JSON, default=list)  # [{name, level}]
    profile = relationship("JobProfile")


class Position(Base):
    __tablename__ = "positions"
    id: Mapped[int] = mapped_column(primary_key=True)
    position_code: Mapped[str] = mapped_column(String(64), unique=True)
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("job_profiles.id"), nullable=True)
    org_unit_id: Mapped[int | None] = mapped_column(ForeignKey("org_units.id"), nullable=True)
    incumbent_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    is_vacant: Mapped[bool] = mapped_column(Boolean, default=False)


# ------------------------------------------------------------------ system
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(128), unique=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(32), default="employee")  # admin|hr|manager|employee
    password_hash: Mapped[str] = mapped_column(String(255), default="")


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(128), index=True)
    # review_due|approval_pending|profile_expired|competency_changed|grade_changed|
    # workflow_assigned|manager_review|employee_request
    notif_type: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(Text)
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("job_profiles.id"), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(128), index=True)
    action: Mapped[str] = mapped_column(String(64))
    entity: Mapped[str] = mapped_column(String(64), default="")
    entity_id: Mapped[str] = mapped_column(String(64), default="")
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
