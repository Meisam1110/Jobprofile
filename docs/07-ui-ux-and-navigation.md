# UI/UX Design, Navigation Map & Wireframes

## Design language

- **Brand**: MTN yellow `#FFCB05` for identity moments (sidebar active state, primary
  brand buttons, current-role card); near-black `#1A1A1A` chrome. Charts use a
  validated colorblind-safe palette (blue/aqua/violet series, sequential blue ramp for
  the heat map) — brand yellow is never a data color.
- **Layout**: fixed dark sidebar (5 destinations), light content plane, card surfaces,
  system font stack. Everything important within two clicks.
- **Patterns**: Fiori-like list → object pattern; object pages use tabs, not scroll
  walls; tables for enumerable facts; badges for status; inline validation errors.

## Navigation map

```
Login (role picker)
└── Shell (sidebar + global search + notifications)
    ├── Dashboard ................ executive analytics, click-through to filtered lists
    ├── Job Profiles ............. repository list (filters: keyword/division/level/status)
    │   ├── + New job profile .... editor (AI draft from title)
    │   └── Profile page ......... header: status, level, exports, Compare, Use-as-template, Edit
    │       ├── Overview ......... Mission · Context · Collaboration · Authorities ·
    │       │                      Working Condition · Performance Standards · Signoff
    │       ├── Responsibilities . numbered statements, % time, deliverables
    │       ├── Competencies ..... technical table (type/level dots) · Live Y'ello chips · skills matrix
    │       ├── Qualifications ... education/experience/trainings groups + KPIs
    │       ├── Career Path ...... previous ← current → next cards, lateral moves
    │       ├── Workflow ......... actions + comment/signature, version history, activity trail
    │       └── AI Assistant ..... quick actions + chat with this profile + similar profiles
    ├── Compare .................. two-profile pickers → highlighted diff report
    ├── AI Assistant ............. standalone: generate/convert/recommend/estimate/translate
    ├── Import / Export .......... master import, bulk upload, template download, Excel export
    └── Administration ........... duplicate scan, review housekeeping, audit log (admin)
```

## Screen wireframes (as built)

**Dashboard** — stat tiles (total, awaiting approval, outdated, career coverage,
missing grade) → grade column chart + division bars → workflow donut + top
competencies → family × grade heat map → largest families. Tiles and bars click
through to pre-filtered repository views.

**Repository** — filter bar (keyword, division, level, status, clear) above a dense
table (title+code+location, division, level badge, reports-to, status pill, version);
row click opens the profile; pagination footer.

**Profile page** — identity header (title, status pill, code · division · location ·
document version) with action row (PDF/Word/JSON/Compare/Use-as-template/Edit), meta
grid (level/band, reports-to, subordinates, employment, families, approval date), then
the tab set above.

**Editor** — sectioned cards mirroring the template order; "✨ AI draft from title"
fills mission/context/responsibilities/competencies/requirements from the corpus (or
Claude when configured); dynamic row editors for responsibilities/competencies/KPIs;
change-note field feeds version history.

**Compare** — two autocomplete pickers; changed-only field table (amber ≠ rows),
competency only-A/shared/only-B columns, responsibilities side-by-side.

**AI Assistant** — task cards on the left (each labeled with what it needs), input +
result viewer right; provider badge shows anthropic vs heuristic provenance.

**Import/Export** — one-click master import, drag-in bulk upload with template link,
bulk Excel export, API pointers. Result banner reports created/updated/skipped.

**Admin** — duplicate scan list (pairs with % similarity, deep links), review scan,
backup notes, audit table.

Screenshots of the running system are reproducible via the Playwright script pattern in
the verification section of the installation guide.

## Accessibility

- Legible ink hierarchy tokens; status never color-alone (pills carry text).
- Heat-map cells and chart bars have title tooltips; tables mirror all chart data.
- Keyboard: all actions are buttons/links; forms label every field.
