# Functional & Non-Functional Requirements

## Functional requirements

### FR-1 Repository (Module 1)
- Central library of all job profiles; active/inactive status; archive (soft delete)
- Version history — every save creates an immutable snapshot with change note and author
- Duplicate detection (similarity scan across active profiles)
- Templates: any profile can be duplicated as a starting point ("Use as template")
- Bulk import from Excel (master-workbook format), idempotent re-import (updates, never duplicates)
- API import (REST); blank Excel import template downloadable
- Multi-language field on profiles; AI-assisted translation
- Full-text search across all template sections + competency names; semantic (TF-IDF) fallback; autocomplete

### FR-2 Job information (Module 2)
Job title, job code, position code, role family, job family, sub family, grade
(Irancell levels 1/2/2H/3/3H/4/5), band, organizational level, division, department,
location, employment type, reporting line, number of subordinates, job category,
FLSA (optional), language.

### FR-3 Job purpose (Module 3)
Mission (position summary) and Context per the official template, plus business value
and success definition fields.

### FR-4 Responsibilities (Module 4)
Ordered responsibility statements with optional % of time, frequency
(daily/weekly/monthly), key tasks, deliverables, decision authority.

### FR-5 KPIs (Module 5)
Individual / Team / Department / Strategic KPIs with weight, owner, formula,
measurement method.

### FR-6 Competencies (Module 6)
Types: Technical, Behavioral, Leadership, Digital, AI, Future. Technical competencies
carry the Irancell categories (General Business / Functional / Specialized Knowledge)
and levels (Basic / Intermediate / Advanced / Expert); each assignment has required
level, desired level, importance, assessment method. Behavioral competencies default to
the Live Y'ello values.

### FR-7 Qualifications (Module 7)
Education, experience, certifications, languages, software knowledge, licenses,
mandatory training, preferred qualifications — each mandatory or preferred.

### FR-8 Skills matrix (Module 8)
Required / preferred / future skills at levels 1–5; gap analysis via profile
comparison and AI "find missing skills".

### FR-9 Organizational relationships (Module 9)
Structured collaboration block parsed from the template: direct reports, matrix
reports, key customers, key suppliers, relations; free-text for committees/forums.

### FR-10 Authority matrix (Module 10)
Authorities text per template ("As per Delegation of authority") plus structured
authority rows (area, authority, limit) for financial/approval/hiring/contract rights.

### FR-11 Career paths (Module 11)
Directed edges between profiles (next / lateral) with promotion criteria and readiness
level; auto-derived ladder within each job family at import; editable by HR.

### FR-12 Success profile (Module 12)
JSON block: top performer characteristics, behavior indicators, critical experiences,
success factors, failure risks.

### FR-13 Learning & development (Module 13)
Mandatory/recommended courses, certifications, learning paths, development plans,
coaching, mentoring — seeded from the template's Trainings section.

### FR-14 Work conditions (Module 14)
Template working-condition text plus structured mode (office/hybrid/remote), travel,
shift, hours, physical requirements, environment.

### FR-15 AI assistant (Module 15)
Tasks: generate profile (from title), convert existing JD, improve writing, recommend
competencies/KPIs/responsibilities/qualifications, estimate grade, suggest career path,
suggest learning, find missing skills, find similar profiles, benchmark, executive
summary, translate, chat with profile. Dual provider: Claude API (generative, grounded
in similar corpus profiles) with automatic fallback to corpus mining when no key is set.

### FR-16 Workflow
States: Draft, Under Review, HR Review, Business Review, Organization Design Review,
Compensation Review, Executive Approval, Published, Archived. Role-gated transitions,
comments, change requests, signature notes, full event trail; publishing snapshots a
version and sets the next review date (+24 months).

### FR-17 Notifications
Raised on workflow assignment, approval pending, review due, profile expired; in-app
notification center; housekeeping scan generates due/expired alerts.

### FR-18 Analytics
Dashboard: total/active profiles, by status/grade/division/family, top competencies,
competency type distribution, outdated (>2y) count, awaiting approval, average review
age, career-path coverage, missing grades, family × grade heat map, duplicate report.

### FR-19 Comparison
Two-profile diff: header fields, grades, all template sections (differences
highlighted), competency overlap with level deltas, responsibilities, KPIs,
qualifications side by side.

### FR-20 Reporting & export
Per profile: PDF, Word (mirrors the official template layout), JSON. Bulk: Excel export
with filters. API returns everything for Power BI/downstream consumption.

### FR-21 Administration
Roles employee < manager < hr < admin; audit log of every mutating action; custom
fields (JSON) per profile; backup/restore guidance; configuration via environment.

### FR-22 Self-service
Employees: view/search profiles, career paths, download PDF, suggest changes
(change-request workflow event). Managers: review/approve, compare team roles. HR:
full lifecycle, imports, reports, workflow management.

## Non-functional requirements

| Attribute | Requirement | v1 implementation |
|---|---|---|
| Scale | 10,000+ profiles | Paginated queries + indexed columns; TF-IDF index ~O(n) memory; OpenSearch adapter path documented |
| Performance | List/filter < 500 ms; search < 1 s | Verified on 1,446 profiles (list ~50 ms, semantic search ~150 ms warm) |
| Availability | Standard business SLA | Stateless API → horizontal scaling behind a load balancer |
| Security | RBAC, audited writes, signed tokens | HMAC tokens; role checks server-side; audit log; SSO/Entra swap-in documented |
| Data integrity | No silent overwrites | Versions are immutable snapshots; workflow transitions validated server-side |
| Portability | SQLite dev → PostgreSQL prod | Single `JPMS_DATABASE_URL` switch |
| Usability | HR-friendly, ≤ 2 clicks to any function | 5-item navigation, global search, no modal mazes |
| Auditability | Who/what/when for every change | `audit_logs` + `workflow_events` + `profile_versions` |
| Internationalization | Multi-language profiles | `language` field + AI translation; RTL-ready system font stack |
