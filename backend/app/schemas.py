"""Pydantic schemas (API contracts)."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------- taxonomy
class GradeOut(ORMModel):
    id: int
    code: str
    rank: int
    band: str = ""


class RoleFamilyOut(ORMModel):
    id: int
    name: str


class JobFamilyOut(ORMModel):
    id: int
    name: str
    role_family_id: int | None = None


class OrgUnitOut(ORMModel):
    id: int
    name: str
    code: str = ""
    unit_type: str = "department"
    parent_id: int | None = None


class CompetencyOut(ORMModel):
    id: int
    name: str
    comp_type: str
    category: str = ""


class SkillOut(ORMModel):
    id: int
    name: str
    category: str = ""


# --------------------------------------------------------- profile parts
class ResponsibilityIn(BaseModel):
    text: str
    pct_time: float | None = None
    frequency: str = ""
    key_tasks: str = ""
    deliverables: str = ""
    decision_authority: str = ""
    sort_order: int = 0


class ResponsibilityOut(ResponsibilityIn, ORMModel):
    id: int


class KPIIn(BaseModel):
    name: str
    kpi_type: str = "Individual"
    weight: float | None = None
    owner: str = ""
    formula: str = ""
    measurement_method: str = ""


class KPIOut(KPIIn, ORMModel):
    id: int


class ProfileCompetencyIn(BaseModel):
    name: str
    comp_type: str = "Technical"
    category: str = ""
    required_level: str = ""
    desired_level: str = ""
    importance: str = ""
    assessment_method: str = ""


class ProfileCompetencyOut(ORMModel):
    id: int
    competency: CompetencyOut
    required_level: str = ""
    desired_level: str = ""
    importance: str = ""
    assessment_method: str = ""


class ProfileSkillIn(BaseModel):
    name: str
    requirement: str = "required"
    level: int = 3
    category: str = ""


class ProfileSkillOut(ORMModel):
    id: int
    skill: SkillOut
    requirement: str
    level: int


class QualificationIn(BaseModel):
    qual_type: str
    text: str
    mandatory: bool = True


class QualificationOut(QualificationIn, ORMModel):
    id: int


class CareerPathIn(BaseModel):
    to_profile_id: int
    path_type: str = "next"
    promotion_criteria: str = ""
    readiness_level: str = ""


class CareerPathEdge(BaseModel):
    id: int
    profile_id: int
    title: str
    grade: str = ""
    path_type: str
    direction: str  # incoming|outgoing
    promotion_criteria: str = ""
    readiness_level: str = ""


# --------------------------------------------------------------- profile
class ProfileBase(BaseModel):
    job_title: str
    job_code: str = ""
    position_code: str = ""
    sub_family: str = ""
    band: str = ""
    org_level: str = ""
    location: str = ""
    employment_type: str = "Full-time"
    reports_to: str = ""
    direct_reports: int = 0
    job_category: str = ""
    flsa_status: str = ""
    language: str = "en"
    grade_code: str | None = None
    role_family: str | None = None
    job_family: str | None = None
    division: str | None = None
    department: str | None = None
    mission: str = ""
    context: str = ""
    business_value: str = ""
    success_definition: str = ""
    responsibilities_text: str = ""
    collaboration_text: str = ""
    authorities_text: str = ""
    education_text: str = ""
    experience_text: str = ""
    trainings_text: str = ""
    behavioral_text: str = ""
    working_conditions: str = ""
    performance_standards: str = ""
    collaboration: dict[str, Any] = Field(default_factory=dict)
    authority_matrix: list[Any] = Field(default_factory=list)
    success_profile: dict[str, Any] = Field(default_factory=dict)
    work_conditions: dict[str, Any] = Field(default_factory=dict)
    signoff: dict[str, Any] = Field(default_factory=dict)
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class ProfileCreate(ProfileBase):
    responsibilities: list[ResponsibilityIn] = Field(default_factory=list)
    kpis: list[KPIIn] = Field(default_factory=list)
    competencies: list[ProfileCompetencyIn] = Field(default_factory=list)
    skills: list[ProfileSkillIn] = Field(default_factory=list)
    qualifications: list[QualificationIn] = Field(default_factory=list)
    change_note: str = ""


class ProfileUpdate(ProfileCreate):
    job_title: str | None = None  # everything optional on update


class ProfileSummary(ORMModel):
    id: int
    job_title: str
    job_code: str = ""
    location: str = ""
    reports_to: str = ""
    direct_reports: int = 0
    status: str
    is_active: bool
    version: int
    updated_at: datetime
    approved_date: datetime | None = None
    grade: GradeOut | None = None
    role_family: RoleFamilyOut | None = None
    job_family: JobFamilyOut | None = None
    division: OrgUnitOut | None = None
    department: OrgUnitOut | None = None


class ProfileDetail(ProfileSummary):
    position_code: str = ""
    sub_family: str = ""
    band: str = ""
    org_level: str = ""
    employment_type: str = ""
    job_category: str = ""
    flsa_status: str = ""
    language: str = "en"
    mission: str = ""
    context: str = ""
    business_value: str = ""
    success_definition: str = ""
    responsibilities_text: str = ""
    collaboration_text: str = ""
    authorities_text: str = ""
    education_text: str = ""
    experience_text: str = ""
    trainings_text: str = ""
    behavioral_text: str = ""
    working_conditions: str = ""
    performance_standards: str = ""
    collaboration: dict[str, Any] = Field(default_factory=dict)
    authority_matrix: list[Any] = Field(default_factory=list)
    success_profile: dict[str, Any] = Field(default_factory=dict)
    work_conditions: dict[str, Any] = Field(default_factory=dict)
    signoff: dict[str, Any] = Field(default_factory=dict)
    custom_fields: dict[str, Any] = Field(default_factory=dict)
    document_version: str = "1.0"
    source_file: str = ""
    created_at: datetime
    responsibilities: list[ResponsibilityOut] = Field(default_factory=list)
    kpis: list[KPIOut] = Field(default_factory=list)
    profile_competencies: list[ProfileCompetencyOut] = Field(default_factory=list)
    profile_skills: list[ProfileSkillOut] = Field(default_factory=list)
    qualifications: list[QualificationOut] = Field(default_factory=list)


class PagedProfiles(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProfileSummary]


# --------------------------------------------------------------- workflow
class WorkflowAction(BaseModel):
    action: str  # submit|approve|reject|publish|archive|comment|request_change|sign
    comment: str = ""
    signature: str = ""


class WorkflowEventOut(ORMModel):
    id: int
    event_type: str
    from_state: str = ""
    to_state: str = ""
    actor: str = ""
    actor_role: str = ""
    comment: str = ""
    created_at: datetime


class VersionOut(ORMModel):
    id: int
    version_no: int
    change_note: str = ""
    changed_by: str = ""
    created_at: datetime


class NotificationOut(ORMModel):
    id: int
    notif_type: str
    message: str
    profile_id: int | None = None
    is_read: bool
    created_at: datetime


# --------------------------------------------------------------------- AI
class AIRequest(BaseModel):
    task: str
    profile_id: int | None = None
    job_title: str | None = None
    text: str | None = None
    target_language: str | None = None
    question: str | None = None


class AIResponse(BaseModel):
    task: str
    provider: str  # "anthropic" | "heuristic"
    result: Any


# ------------------------------------------------------------------- auth
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    full_name: str
    role: str
