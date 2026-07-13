# Database Design & ER Diagram

Normalized around the **job profile as master record**. Long template sections are kept
verbatim (fidelity to the official document) *and* parsed into structured child rows
(analytics/AI) — the same duality the organization already practices between Word
profiles and the master workbook, now governed in one place.

## ER diagram

```mermaid
erDiagram
    ORG_UNIT ||--o{ ORG_UNIT : "parent of"
    ORG_UNIT ||--o{ JOB_PROFILE : "division / department"
    ROLE_FAMILY ||--o{ JOB_FAMILY : contains
    ROLE_FAMILY ||--o{ JOB_PROFILE : classifies
    JOB_FAMILY ||--o{ JOB_PROFILE : groups
    GRADE ||--o{ JOB_PROFILE : levels

    JOB_PROFILE ||--o{ RESPONSIBILITY : "has ordered"
    JOB_PROFILE ||--o{ PROFILE_KPI : measures
    JOB_PROFILE ||--o{ PROFILE_COMPETENCY : requires
    COMPETENCY ||--o{ PROFILE_COMPETENCY : "assigned as"
    JOB_PROFILE ||--o{ PROFILE_SKILL : needs
    SKILL ||--o{ PROFILE_SKILL : "assigned as"
    JOB_PROFILE ||--o{ QUALIFICATION : demands
    JOB_PROFILE ||--o{ LEARNING_ITEM : develops
    JOB_PROFILE ||--o{ CAREER_PATH : "from / to"
    JOB_PROFILE ||--o{ PROFILE_VERSION : "snapshots"
    JOB_PROFILE ||--o{ WORKFLOW_EVENT : "approval trail"
    JOB_PROFILE ||--o{ ATTACHMENT : stores

    EMPLOYEE }o--|| JOB_PROFILE : "holds role"
    EMPLOYEE }o--o| EMPLOYEE : "reports to"
    POSITION }o--|| JOB_PROFILE : instantiates
    POSITION }o--o| ORG_UNIT : "sits in"
    POSITION }o--o| EMPLOYEE : "filled by"

    USER ||--o{ NOTIFICATION : receives
    USER ||--o{ AUDIT_LOG : acts

    JOB_PROFILE {
        int id PK
        string job_title
        string job_code
        string position_code
        string location "template: Location of the Job"
        string reports_to
        int direct_reports "template: Number of subordinates"
        string org_level "raw level text"
        int grade_id FK
        int role_family_id FK
        int job_family_id FK
        int division_id FK
        int department_id FK
        text mission "template section"
        text context "template section"
        text responsibilities_text "verbatim section"
        text collaboration_text
        json collaboration "parsed: direct/matrix/customers/suppliers"
        text authorities_text
        json authority_matrix
        text education_text
        text experience_text
        text trainings_text
        text behavioral_text
        text working_conditions
        text performance_standards
        json signoff "LM/FM/OA/HoD/CHRO/CEO"
        json success_profile
        json work_conditions
        json custom_fields "dynamic metadata"
        string status "workflow state"
        bool is_active
        int version
        string document_version
        datetime approved_date
        datetime next_review_date
        string source_file "import idempotency key"
    }
    GRADE { int id PK  string code "1,2,2H,3,3H,4,5"  int rank  string band }
    COMPETENCY { int id PK  string name  string comp_type "Technical/Behavioral/Leadership/Digital/AI/Future"  string category "GBK/FK/SK" }
    PROFILE_COMPETENCY { int id PK  string required_level "Basic..Expert"  string desired_level  string importance  string assessment_method }
    PROFILE_SKILL { int id PK  string requirement "required/preferred/future"  int level "1-5" }
    RESPONSIBILITY { int id PK  text text  float pct_time  string frequency  text deliverables  text decision_authority  int sort_order }
    PROFILE_KPI { int id PK  string name  string kpi_type "Individual/Team/Department/Strategic"  float weight  string formula  string measurement_method }
    QUALIFICATION { int id PK  string qual_type "education/experience/certification/language/software/license/training/preferred"  text text  bool mandatory }
    CAREER_PATH { int id PK  string path_type "next/lateral"  text promotion_criteria  string readiness_level }
    PROFILE_VERSION { int id PK  int version_no  json snapshot  text change_note  string changed_by }
    WORKFLOW_EVENT { int id PK  string event_type "transition/comment/change_request/signature"  string from_state  string to_state  string actor  string actor_role  text comment  string signature }
    AUDIT_LOG { int id PK  string actor  string action  string entity  string entity_id  json detail }
```

## Key relationships explained

- **Grade** encodes the Irancell level structure as first-class data: `code` is what HR
  writes ("3H"), `rank` makes it sortable, `band` gives the human meaning. Profiles keep
  the raw text in `org_level` too, so nothing from the source workbook is lost.
- **Role family ← Job family ← Profile** mirrors the organization's architecture: role
  families derive from divisions (Network Group, Finance, …); job families from the
  functional stem of titles (e.g. "Access Transmission Planning and Optimization"), which
  is also what powers auto-derived **career ladders** — edges connect profiles within a
  family ordered by title seniority (Engineer → Specialist → Senior Specialist →
  Manager → Senior Manager → General Manager).
- **Competency** is a shared catalog (deduplicated by name+type), so "Network Planning
  and Design" is one row referenced by hundreds of profiles — this is what makes
  competency analytics and gap analysis possible.
- **ProfileVersion.snapshot** stores the full serialized profile (same shape as the JSON
  export), making versions self-contained and restorable without schema archaeology.
- **WorkflowEvent** is append-only; the profile's `status` is the current state, the
  events are the proof.
- **source_file** is the import idempotency key: re-importing the master workbook
  updates matching profiles in place.
- **Employee / Position** are integration surfaces: JPMS does not own people data, it
  links to it so "find internal successors / who holds this role" queries work when the
  HRIS sync is connected.

## Indexing

Foreign keys, `job_profiles.job_title`, `job_code`, `status` and audit timestamps are
indexed. For PostgreSQL production add a `tsvector` GIN index over the text sections
(or route search to OpenSearch) beyond ~10k profiles.
