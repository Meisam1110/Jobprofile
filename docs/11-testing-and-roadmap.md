# Testing Strategy & Future Roadmap

## Testing strategy

### Implemented (backend/tests/test_api.py — run `python -m pytest tests/ -q`)
- **Auth & RBAC**: bad credentials rejected; employee blocked from HR endpoints.
- **Profile lifecycle**: create with full child payload → grade/taxonomy resolution →
  update bumps version → snapshot integrity.
- **Workflow**: full chain Draft→…→Published; invalid transition returns 400.
- **Exports**: JSON/Word/PDF return correct content types and non-empty bodies.
- **Search**: created profiles are findable.
- **Duplicate & compare**: template-clone flow, diff flags.
- **AI**: heuristic provider responds for grade estimation and recommendations.
- **Dashboard**: aggregate shape sanity.

### Verified manually in this build
- Real-data import: 1,446 profiles / 25,667 competency links parsed from the master
  workbook; spot-checked titles, grades, collaboration parsing, competency triples.
- UI walkthrough via headless Chromium: login, dashboard charts with real
  aggregates, repository filters, profile tabs, AI panel, exports.

### Recommended additions before enterprise rollout
1. **Frontend tests**: Playwright E2E on the golden paths (login→search→profile→
   export; HR create→workflow→publish); component tests for editors.
2. **Import property tests**: fuzz the workbook parser (merged cells, RTL text,
   missing columns) — it must skip, never corrupt.
3. **Load tests**: k6/locust at 10k profiles, 100 concurrent users; assert list
   < 500 ms, search < 1 s.
4. **Security**: dependency audit in CI, authz matrix tests per endpoint × role,
   upload handling (size caps, content-type).
5. **AI evaluation set**: ~50 curated title→expected-grade/competency cases; score
   provider changes against it.

## Future roadmap

**Phase 2 — Organization integration (next quarter)**
- HRIS/ERP sync for org units, positions, employees → live vacancy and incumbent views
- Entra ID SSO + AD group role mapping
- Org-chart visualization from reporting lines; position-to-profile coverage report
- Teams/Outlook notification connectors; PowerPoint export of profile summaries

**Phase 3 — Talent processes**
- Succession: successor slates from career-path graph + employee skill matching
  ("find internal successors" backed by real employee data)
- Recruitment: requisition generation into the ATS from published profiles
- Learning: push competency gaps to the LMS as learning-path assignments
- Employee self-service portal: my profile vs target role gap view

**Phase 4 — Intelligence at scale**
- OpenSearch/Elasticsearch for search + embeddings (semantic search beyond TF-IDF)
- Claude-powered batch quality review: flag stale language, inconsistent grading,
  missing sections across the whole library
- Future-skills prediction from industry taxonomies (ESCO/O*NET mapping)
- Compensation benchmarking integration (Mercer IPE / Korn Ferry leveling cross-walk)
- Persian (Farsi) full UI localization with RTL layout

**Platform hardening (continuous)**
- Redis caching for dashboard aggregates; background jobs (imports, scans) via a queue
- Attachment storage on S3-compatible object store; template versioning per document
- GraphQL read layer if downstream consumers need shaped queries
