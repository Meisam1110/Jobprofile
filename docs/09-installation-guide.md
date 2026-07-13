# Installation Guide

## Prerequisites
- Python 3.11+
- Node.js 20+
- (Production) PostgreSQL 14+; (optional) an Anthropic API key for generative AI

## Local / demo install

```bash
git clone <repo> && cd Jobprofile

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate     # recommended
pip install -r requirements.txt
cd ..

# Seed the database from the master workbook (~30 s, idempotent)
python scripts/import_excel.py

# Frontend
cd frontend
npm install
npm run build           # -> frontend/dist (served automatically by the API)
cd ..

# Run
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 — sign in as `hr` / `demo` (also `admin`, `manager`,
`employee`). API reference: http://localhost:8000/docs.

### Frontend development mode
`cd frontend && npm run dev` → http://localhost:5173 with hot reload
(`/api` proxied to :8000).

## Configuration (environment variables, prefix `JPMS_`)

| Variable | Default | Purpose |
|---|---|---|
| `JPMS_DATABASE_URL` | `sqlite:///backend/jobprofile.db` | e.g. `postgresql+psycopg2://user:pass@host/jpms` |
| `JPMS_AUTH_SECRET` | change-me | HMAC secret for demo tokens — set in prod or replace with SSO |
| `JPMS_ANTHROPIC_API_KEY` | (empty) | Enables generative AI (drafting, rewriting, translation, chat) |
| `JPMS_ANTHROPIC_MODEL` | `claude-sonnet-5` | Model for AI tasks |
| `JPMS_CORS_ORIGINS` | `["*"]` | Restrict in production |

## Production deployment

```bash
# PostgreSQL
export JPMS_DATABASE_URL=postgresql+psycopg2://jpms:***@db:5432/jpms
pip install psycopg2-binary
python scripts/import_excel.py                     # one-time seed
gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 app.main:app
```

- Put the app behind a reverse proxy (nginx/Traefik) with TLS.
- Schedule `POST /api/admin/review-scan` (cron/Task Scheduler) for review-due alerts.
- Backups: `pg_dump` nightly; SQLite demos: `sqlite3 jobprofile.db ".backup ..."`.
- SSO/Entra ID swap: see `docs/06-workflow-and-security.md`.

### Docker (optional pattern)

```dockerfile
FROM node:20 AS ui
WORKDIR /app/frontend
COPY frontend/package*.json ./ && RUN npm ci
COPY frontend .
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt backend/
RUN pip install -r backend/requirements.txt
COPY backend backend
COPY data data
COPY scripts scripts
COPY --from=ui /app/frontend/dist frontend/dist
WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Verification

```bash
cd backend && python -m pytest tests/ -q     # 5 API tests: auth/RBAC, lifecycle,
                                             # workflow, exports, search, AI, dashboard
curl -s localhost:8000/api/health            # {"status":"ok"}
curl -s "localhost:8000/api/analytics/dashboard" | head -c 200
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: _cffi_backend` (fpdf/cryptography) | `pip install --upgrade cffi cryptography` |
| Frontend 404 at `/` | Build the frontend (`npm run build`) or use dev mode on :5173 |
| Import finds no sheet | Workbook must contain `Job_Profile_Data` (header row 8) — use the template from `/api/import/template` |
| AI returns `provider: heuristic` | Expected without `JPMS_ANTHROPIC_API_KEY`; corpus mode is fully functional |
