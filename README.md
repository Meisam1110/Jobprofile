# Irancell Enterprise Job Profile Management System (JPMS)

The **single source of truth** for every job profile at MTN Irancell — job architecture,
competencies, approval workflow, analytics, comparison and AI assistance, built directly
on the organization's own data:

- **`data/job_profiles_master.xlsm`** — the master workbook (1,446 job profiles) that seeds the system
- **`data/job_profile_template.docx`** — the official Irancell job profile template whose
  sections (Mission, Context, Roles & Responsibilities, Collaboration, Authorities,
  Education, Experience, Technical/Behavioral Competencies, Trainings, General Working
  Condition, Performance Standards, Signoff) drive the data model, UI and exports

## Quick start

```bash
# 1. Backend (Python 3.11+)
cd backend
pip install -r requirements.txt
cd ..
python scripts/import_excel.py          # seed the DB from the master workbook (~30 s)

# 2. Frontend (Node 20+)
cd frontend
npm install
npm run build                            # outputs frontend/dist, served by the API
cd ..

# 3. Run
cd backend
uvicorn app.main:app --port 8000
# App:      http://localhost:8000        (login: hr / demo — also admin, manager, employee)
# API docs: http://localhost:8000/docs
```

For frontend development with hot reload: `npm run dev` in `frontend/` (proxies `/api` to :8000).

**Optional AI provider:** set `JPMS_ANTHROPIC_API_KEY` to enable generative drafting,
rewriting, translation and free-form chat via the Claude API. Without a key, every AI
feature still works in *corpus mode* (recommendations mined from the imported profiles).

## What's inside

| Area | Highlights |
|---|---|
| Repository | 1,446 imported profiles, filters, full-text + semantic search, autocomplete, duplicate detection, use-as-template, soft archive |
| Job profile | All official template sections + KPIs, skills matrix, qualifications, career paths, versions |
| Workflow | Draft → Under Review → HR → Business → Organization Design → Compensation → Executive Approval → Published → Archived, with comments, digital-signature notes, change requests, full audit trail |
| Analytics | Executive dashboard: totals, by grade/division/family, competency distribution, outdated profiles, career-path coverage, family × grade heat map |
| Compare | Field-by-field diff, competency overlap, responsibilities/KPIs/qualifications side-by-side |
| AI assistant | Generate profile, convert JD, recommend competencies/KPIs/responsibilities/qualifications, estimate grade, career path, missing skills, benchmark, executive summary, translation, chat with a profile |
| Import/Export | Master-workbook import (idempotent), bulk Excel upload + blank template, Word/PDF/JSON per profile (Word mirrors the official template), Excel bulk export |
| Administration | Role-based access (employee < manager < hr < admin), audit log, review housekeeping, notifications |

## Repository layout

```
backend/    FastAPI app — models, routers, services (importer, AI, exporter, workflow), tests
frontend/   React 18 + TypeScript + Tailwind (Vite)
data/       Master workbook + official template (the system's foundation)
docs/       Full documentation set (architecture, ER diagram, API spec, guides, roadmap)
scripts/    import_excel.py — CLI seed/refresh from the workbook
```

## Documentation

See [`docs/`](docs/): executive summary & vision, functional/non-functional requirements,
system architecture, database design + ER diagram, API specification, AI architecture,
workflow & security model, UI/UX & navigation, template mapping, installation & user
guides, testing strategy and roadmap.

## Production notes

- **Database**: defaults to SQLite for zero-setup demos; set `JPMS_DATABASE_URL` to a
  PostgreSQL URL for production (SQLAlchemy models are dialect-neutral).
- **Auth**: demo login is HMAC-token based; swap for SSO / Microsoft Entra ID per
  `docs/06-workflow-and-security.md`.
- **Search**: SQL + in-memory TF-IDF today; OpenSearch/Elasticsearch adapter path is
  documented in the architecture doc for 10k+ profile scale.

Run tests: `cd backend && python -m pytest tests/ -q`
