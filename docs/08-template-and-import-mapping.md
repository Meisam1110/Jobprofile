# Job Profile Template Mapping & Excel Import

## Official template → system mapping

Every section of `data/job_profile_template.docx` (the official Irancell job profile)
maps 1:1 into the data model and back out through Word/PDF export:

| Template element | System field(s) | Notes |
|---|---|---|
| Header: "MTNIRANCELL · JOB PROFILE · Organization Architecture, HR" | export branding | reproduced in Word/PDF |
| Title of Position | `job_title` | title-repair logic fixes truncations from the workbook |
| Location of the Job | `location` + `department` link | department OrgUnit auto-created |
| Reports to | `reports_to` | |
| Number of subordinates | `direct_reports` | integer-parsed |
| Level | `org_level` (raw) + `grade_id` | normalized to 1/2/2H/3/3H/4/5 |
| Mission | `mission` | |
| Context | `context` | |
| Roles & Responsibilities | `responsibilities_text` (verbatim) + `Responsibility` rows | sentence-split, ordered |
| Collaboration | `collaboration_text` + parsed `collaboration` JSON | anchors: Direct Reports / Matrix Reports to / Key Customers / Key Suppliers / Relations |
| Authorities | `authorities_text` + `authority_matrix` | usually "As per Delegation of authority" |
| Job Requirements → Education | `education_text` + Qualification(education) | |
| Job Requirements → Experience | `experience_text` + Qualification(experience) | |
| Competencies → Technical | `ProfileCompetency` rows | "Title · Type · Level" triples parsed; Type ∈ General Business / Functional / Specialized Knowledge; Level ∈ Basic / Intermediate / Advanced / Expert |
| Competencies → Behavioral | `behavioral_text` + Behavioral `ProfileCompetency` rows | recognizes Live Y'ello values and the legacy vitals list |
| Trainings | `trainings_text` + Qualification(training) | |
| General Working Condition | `working_conditions` | |
| Performance Standards | `performance_standards` | |
| Signoff grid (Line Manager / Functional Manager / OA / HoD / CHRO / CEO-COO) | `signoff` JSON + workflow stages | export reproduces the grid; workflow digitizes the chain |
| Division Approval By / HR Approval By / Approved Date / Document Version | `signoff` + `approved_date` + `document_version` | approved profiles import as **Published** |

## Master workbook import (`data/job_profiles_master.xlsm`)

Sheet **`Job_Profile_Data`**, header on **row 8**, one flattened Word document per row.
Columns consumed: File Name, Title of Position, Location of the Job, Reports to,
Number of Subordinates, Level, Mission, Context, Roles & Responsibilities,
Collaboration, Authorities, Education, Experience, Technical Competencies, Behavioral
Competencies, Trainings, General Working Condition, Performance Standards, Signoff,
Division/HR Approval, Document Version, Approved Date, DIV (division code).

Import behavior (see `backend/app/services/importer.py`):

1. **Cleaning** — Word artifacts (`_x000B_`, `_x000C_`), NBSPs and whitespace runs removed.
2. **Title repair** — when the title cell is a truncated prefix (a known flattening
   artifact, e.g. "Access Trans"), the full title is recovered from the source file name.
3. **Grade normalization** — `3h`→`3H`, `L3H`→`3H`; TBD/Contractor/#N/A → ungraded
   (surfaced on the dashboard as "missing grade").
4. **Division codes** → named divisions (NWG→Network Group, S&D→Sales & Distribution, …,
   30 divisions); departments hang under divisions.
5. **Role family** = division; **job family** = functional stem of the title; both feed
   auto-derived **career ladders** (Engineer → Specialist → Senior Specialist → Manager
   → Senior Manager → General Manager within a family).
6. **Idempotency** — `source_file` is the match key: re-import updates in place,
   child rows are rebuilt, nothing duplicates.
7. Rows with approved dates arrive **Published**; others **Draft**.

Import stats on the bundled workbook: 1,446 profiles, 25,667 competency assignments,
15,546 responsibilities, 30 divisions, ~370 career edges, in ~27 s.

## Bulk-upload Excel template

`GET /api/import/template` produces a simplified single-header workbook (same parser)
with an example row:

Title of Position · Location of the Job · Reports to · Number of Subordinates · Level ·
Mission · Context · Roles & Responsibilities · Collaboration · Authorities · Education ·
Experience · Technical Competencies ("Name Type Level" triples) · Behavioral
Competencies (one per line) · Trainings · General Working Condition · Performance
Standards · Division Code
