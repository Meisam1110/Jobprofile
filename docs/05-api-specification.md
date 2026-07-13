# API Specification

Base URL `/api`. JSON everywhere. Auth: `Authorization: Bearer <token>` from
`/api/auth/login`; unauthenticated requests get read-only employee scope.
Interactive OpenAPI docs at **`/docs`**.

Roles: `employee < manager < hr < admin`. "Min role" below is enforced server-side.

## Auth
| Method | Path | Min role | Description |
|---|---|---|---|
| POST | `/auth/login` | — | `{username, password}` → `{token, role, full_name}` (demo users: admin/hr/manager/employee, password `demo`) |
| GET | `/auth/me` | — | Current identity |

## Taxonomy & lookups
| GET | `/taxonomy` | — | Grades, divisions, role families, job families, statuses, competency types/levels (drives all UI facets) |
| GET | `/competencies?q=&comp_type=&limit=` | — | Competency catalog search |

## Profiles
| Method | Path | Min role | Description |
|---|---|---|---|
| GET | `/profiles` | — | Paged list. Filters: `q, status, grade, division, department, role_family, job_family, active, sort, page, page_size` |
| GET | `/profiles/{id}` | — | Full detail: all template sections + responsibilities, KPIs, competencies, skills, qualifications |
| POST | `/profiles` | hr | Create. Body: `ProfileCreate` (scalar fields + `grade_code`, `division`… names + child lists). Snapshots v1 |
| PUT | `/profiles/{id}` | hr | Update (partial); child lists replace when provided; snapshots a new version with `change_note` |
| POST | `/profiles/{id}/duplicate` | hr | Clone as Draft "(Copy)" — the job-template mechanism |
| DELETE | `/profiles/{id}` | hr | Soft delete (inactive + Archived) |
| GET | `/profiles/{id}/versions` | — | Version list |
| GET | `/profiles/{id}/versions/{no}` | — | Full snapshot of a version |
| GET | `/profiles/{id}/career-path` | — | Incoming/outgoing career edges |
| POST | `/profiles/{id}/career-path` | hr | Add edge `{to_profile_id, path_type, promotion_criteria, readiness_level}` |
| GET | `/profiles/{id}/workflow` | — | Approval trail |
| POST | `/profiles/{id}/workflow` | varies | `{action, comment?, signature?}` — actions: `submit, approve, publish, reject, request_change, archive, restore, comment` (+ explicit `send_to_*`). Invalid transitions → 400; insufficient role → 403 |
| GET | `/profiles/{id}/export?fmt=pdf|docx|json` | — | Single-profile export (Word mirrors the official template) |

## Search
| GET | `/search?q=&limit=&semantic=` | — | Full-text over title/code/sections + competency names; TF-IDF semantic ranking appended when sparse or `semantic=true`. Each hit carries `match` provenance |
| GET | `/search/autocomplete?q=` | — | Title typeahead (10) |

## Analytics
| GET | `/analytics/dashboard` | — | All executive metrics (see requirements FR-18) |
| GET | `/analytics/heatmap` | — | Job family × grade counts (top 25 families) |
| GET | `/analytics/duplicates?threshold=` | — | Similar-pair report (default ≥ 0.82) |

## Compare
| GET | `/compare?a={id}&b={id}` | — | Field diffs with `different` flags, competency only-A/only-B/shared with levels, responsibilities/KPIs/qualifications side-by-side |

## AI
| GET | `/ai/tasks` | — | Task list + whether the generative provider is configured |
| POST | `/ai` | — | `{task, profile_id?, job_title?, text?, question?, target_language?}` → `{provider: "anthropic"|"heuristic", result}`. Tasks: `generate_profile, convert_jd, improve_writing, recommend_competencies, recommend_kpis, recommend_responsibilities, recommend_qualifications, estimate_grade, suggest_career_path, suggest_learning, find_missing_skills, find_similar, benchmark, executive_summary, translate, chat` |
| GET | `/ai/similar/{id}?top=` | — | Nearest profiles with similarity scores |

## Import / Export
| POST | `/import/master` | hr | Import/refresh the bundled `data/job_profiles_master.xlsm` |
| POST | `/import/excel` | hr | Multipart upload of a workbook in master format; returns `{created, updated, skipped, competencies}` |
| GET | `/import/template` | — | Blank Excel bulk-upload template with example row |
| GET | `/export/excel?status=&division=&limit=` | — | Bulk Excel export |

## Notifications & admin
| GET | `/notifications` | — | For current user/role |
| POST | `/notifications/{id}/read` | — | Mark read |
| GET | `/admin/audit?limit=` | admin | Audit log |
| POST | `/admin/review-scan` | hr | Generate review-due / expired notifications |
| GET | `/health` | — | Liveness |

### Error model
`{"detail": "..."}` with appropriate status: 400 invalid transition/payload,
401 bad credentials, 403 insufficient role, 404 missing entity.
