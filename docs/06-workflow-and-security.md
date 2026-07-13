# Workflow Design & Security Model

## Approval workflow

Digitizes the signoff chain printed on every Irancell profile (Line Manager /
Functional Manager / OA / HoD / CHRO / CEO-COO) as review stages:

```
Draft ──submit──▶ Under Review ──▶ HR Review ──▶ Business Review
   ▲                                                   │
   │reject / request_change (any review stage)         ▼
   │                              Organization Design Review
   │                                                   │
   │                                                   ▼
   └───────────── Compensation Review ──▶ Executive Approval ──publish──▶ Published
                        └────────────────publish (fast path)──────────────▶   │
                                                                     archive  ▼
                                                                            Archived ──restore──▶ Draft
```

- **`approve`** advances one stage; explicit `send_to_*` actions allow stage skipping
  by authorized roles (e.g. a simple retitle may go HR Review → publish).
- **`reject` / `request_change`** return to Draft with the reason recorded.
- **Publishing** stamps `approved_date`, sets `next_review_date = +24 months`, and
  snapshots an immutable version — the published record is always reconstructable.
- **Digital signature**: transitions accept a `signature` note stored on the event
  (hash/e-sign integration point); the trail shows who signed what, when.
- Every transition, comment and change request is an append-only `WorkflowEvent`.

### Role gates (server-enforced)

| Action | Minimum role |
|---|---|
| submit, request_change, comment | employee |
| approve, reject, send_to_business/od | manager |
| publish, archive, restore, send_to_hr/comp/executive | hr |
| audit log | admin |

### Notifications
Workflow moves notify the HR queue; the housekeeping scan
(`POST /api/admin/review-scan`) raises `review_due` (past `next_review_date`) and
`profile_expired` (> 2 years since approval) alerts — schedule it via cron.

## Security model

### Authentication
v1 demo: HMAC-SHA256-signed bearer tokens (`security.py`), constant-time verified,
secret via `JPMS_AUTH_SECRET`. **Production swap (designed-in):** replace
`get_current_user` with OIDC validation against **Microsoft Entra ID** (or AD FS):
validate the JWT, map AD groups → app roles, everything downstream is unchanged.
SSO section for implementers:

1. Register the app in Entra ID (SPA + API), expose `api://jpms` scope.
2. Frontend: MSAL acquires tokens; replace the login page.
3. Backend: verify `iss/aud/exp` + signature via JWKS; map `groups`/`roles` claims to
   `employee|manager|hr|admin`.

### Authorization
Single ordered role model enforced in FastAPI dependencies (`require_role`), never in
the client. Workflow actions carry their own role gates.

### Data protection
- All writes audited (`audit_logs`: actor, action, entity, JSON detail, timestamp).
- Versions immutable; deletes are soft (`is_active=false`), preserving history.
- Secrets only via environment (`JPMS_ANTHROPIC_API_KEY`, `JPMS_AUTH_SECRET`,
  `JPMS_DATABASE_URL`); nothing sensitive in the repo.
- CORS configurable (`JPMS_CORS_ORIGINS`); default open for dev, restrict in prod.
- SQL injection prevented by ORM-parameterized queries; uploads size-checked by the
  server and parsed with openpyxl only (`.xlsx/.xlsm`), never executed (VBA in `.xlsm`
  is ignored by openpyxl).

### Backup / restore
SQLite: file copy of `backend/jobprofile.db` (WAL-safe: `sqlite3 ".backup"`).
PostgreSQL: `pg_dump` schedule + PITR. Application-level: bulk Excel export and
per-profile JSON snapshots provide logical backups.
