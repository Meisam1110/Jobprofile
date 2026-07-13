# System Architecture

## Overview

```
┌────────────────────────────────────────────────────────────────────┐
│  Browser — React 18 + TypeScript + Tailwind (Vite build)           │
│  Dashboard · Repository · Profile · Compare · AI · Import · Admin  │
└──────────────────────────────┬─────────────────────────────────────┘
                               │ REST /api/* (JSON, Bearer token)
┌──────────────────────────────▼─────────────────────────────────────┐
│  FastAPI application (backend/app)                                 │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌──────────────┐            │
│  │ routers/ │ │ services/│ │ security│ │ schemas (v2) │            │
│  │ profiles │ │ importer │ │  RBAC   │ │  Pydantic    │            │
│  │ misc     │ │ ai       │ └─────────┘ └──────────────┘            │
│  │ ai       │ │ exporter │  ┌───────────────────────────────────┐  │
│  │ import/  │ │ similarity│ │ SQLAlchemy 2.0 ORM                │  │
│  │ export   │ │ workflow │  │ SQLite (dev) / PostgreSQL (prod)  │  │
│  └──────────┘ │ versioning│ └───────────────────────────────────┘  │
│               └────┬─────┘                                         │
│                    │ optional HTTPS                                │
│           ┌────────▼─────────┐                                     │
│           │ Claude API       │  (JPMS_ANTHROPIC_API_KEY)           │
│           │ + heuristic      │  automatic offline fallback         │
│           │ corpus engine    │                                     │
│           └──────────────────┘                                     │
└────────────────────────────────────────────────────────────────────┘
        ▲                                   ▲
        │ scripts/import_excel.py           │ /api/import/excel (upload)
   data/job_profiles_master.xlsm      HR bulk uploads
```

Single-container deployment: the API serves the built frontend from `frontend/dist`.
Scale-out: run N stateless API replicas against PostgreSQL; move the TF-IDF index to
OpenSearch when the corpus outgrows memory (adapter seam is `services/similarity.py` +
`/api/search`).

## Folder structure

```
backend/
  app/
    main.py            FastAPI entry; mounts routers + static frontend
    config.py          Pydantic settings (JPMS_* env vars)
    database.py        Engine/session; SQLite pragmas; Postgres-ready
    models.py          Full ORM (see 04-database-design.md)
    schemas.py         API contracts
    security.py        Demo auth + RBAC dependency (SSO swap point)
    routers/
      profiles.py      CRUD, versions, career paths, workflow actions
      misc.py          auth, taxonomy, search, analytics, compare, notifications, admin
      ai.py            AI task dispatch + similarity
      importexport.py  Excel import, Word/PDF/Excel/JSON export
    services/
      importer.py      Master-workbook parser (title repair, competency triples,
                       collaboration anchors, grade normalization, career ladders)
      similarity.py    TF-IDF index: similar profiles, duplicates, grade k-NN
      ai.py            Task orchestration; Claude API + heuristic fallback
      exporter.py      Official-template Word, branded PDF, Excel, JSON
      workflow.py      State machine (states, transitions, role gates)
      versioning.py    Snapshots, audit log, notifications
  tests/test_api.py    End-to-end API tests (in-process, temp DB)
frontend/
  src/api.ts           Typed client + design tokens
  src/App.tsx          Shell: sidebar, global search, notifications, routes
  src/components/charts.tsx  Dataviz primitives (stat tiles, bars, donut, heat map)
  src/pages/           Dashboard, Repository, ProfileDetail, ProfileEdit,
                       Compare, Assistant, ImportExport, Admin, Login
data/                  Master workbook + official template (system foundation)
scripts/import_excel.py
docs/
```

## AI architecture

Two-tier provider behind one interface (`services/ai.py::run_task`):

1. **Retrieval grounding (always on).** For any task, the TF-IDF index retrieves the
   most similar existing Irancell profiles; their briefs become context.
2. **Generation.**
   - *Claude API configured*: task-specific prompts carry the system prompt (official
     template structure, Live Y'ello values, level system) + retrieved briefs;
     JSON-shaped tasks are parsed back into structured recommendations.
   - *No key / API failure*: heuristic engine answers from the corpus alone — competency
     co-occurrence mining, grade k-NN voting with evidence, responsibility harvesting,
     career-path graph reads, template-based executive summaries, keyword-grounded chat.

This guarantees the AI features never dead-end: answers degrade gracefully from
generative to evidence-retrieval, and every recommendation cites its supporting
profiles.

## Integration design

| System | Direction | Mechanism (v1 → target) |
|---|---|---|
| HRIS / ERP | in | Excel import today → scheduled REST sync of org units, positions, employees |
| ATS (recruitment) | out | `GET /api/profiles/{id}` JSON = requisition source of truth |
| LMS | out | Qualifications/trainings per profile feed learning-path assignment |
| Performance | out | KPIs + performance standards per profile |
| Compensation | out | Grade/band + authority matrix |
| Org chart | in/out | `org_units` tree + `positions`; reporting lines on profiles |
| Identity (Entra ID / AD) | in | Replace demo login with OIDC; map AD groups → roles |
| Power BI | out | REST API + Excel export; direct DB read replica for large models |
| Teams / Outlook | out | Notification webhooks (roadmap) |
| Document mgmt | out | Word/PDF exports mirror the official template |

## Performance notes

- List queries are paginated + eager-load taxonomy joins (no N+1).
- The similarity index builds lazily (~2 s for 1,446 profiles) and invalidates on writes.
- Bulk import: 1,446 Word-derived rows parsed + normalized in ~27 s, committed in batches.
- SQLite WAL mode for dev concurrency; production Postgres removes the single-writer limit.
