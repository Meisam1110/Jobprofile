# User Guide

Sign in at the app URL. Demo roles: **hr**, **manager**, **employee**, **admin**
(password `demo`). Your role decides what you can do — the UI hides what you can't.

## Finding a profile
- **Global search** (top bar, any page): type 2+ letters of a title → jump straight to
  a profile.
- **Job Profiles**: filter by keyword, division, level (1–5, 2H/3H) and workflow
  status; click any row. Column "v" is the revision count.
- **Deep search**: keyword search also matches mission, context, responsibilities,
  education, experience and competency names — searching "microwave" finds
  transmission roles even if the word isn't in the title. Natural-language queries get
  semantic matches labeled with their provenance.

## Reading a profile
Tabs mirror the official template:
- **Overview** — Mission, Context, Collaboration (direct/matrix reports, key
  customers/suppliers), Authorities, Working Condition, Performance Standards, Signoff.
- **Responsibilities** — numbered, with % of time and deliverables when defined.
- **Competencies** — technical table with knowledge type and level dots
  (Basic → Expert), Live Y'ello behavioral chips, skills matrix.
- **Qualifications** — education / experience / trainings, plus KPIs.
- **Career Path** — feeder roles ← current → next roles, with readiness; click any
  card to open that profile.
- **Workflow** — current state, allowed actions, version history, full activity trail.
- **AI Assistant** — one-click executive summary, competency recommendations, missing
  skills, grade estimate, benchmark; free chat ("What career path follows this
  role?"); similar-profiles panel.

**Downloads**: PDF / Word / JSON buttons in the header. Word output follows the
official template layout including the signoff grid.

## Creating & editing (HR)
- **New from scratch**: Job Profiles → *+ New job profile*. Type the title, press
  **✨ AI draft from title** — the system pre-fills mission, context,
  responsibilities, competencies and requirements from the most similar existing
  Irancell roles (or Claude, when configured). Adjust, add a change note, Save.
- **New from template**: open a similar profile → **Use as template** → edit the copy.
- **Editing** always records a new version with your change note; nothing is lost.

## Approval workflow
1. Author submits (Draft → Under Review).
2. Reviewers **Approve** through the chain: HR → Business → Organization Design →
   Compensation → Executive Approval (managers can approve early stages; HR publishes).
3. Any reviewer can **Reject to Draft** or **Request changes** with a comment.
4. **Publish** stamps the approval date and schedules the next review (+2 years).
5. Add a comment or signature note on any action — everything lands in the activity
   trail. The bell icon shows workflow items waiting on you.

## Comparing roles
**Compare** (sidebar), or the Compare button on a profile: pick two roles; identical
fields are hidden by default so differences pop — grade, sections (amber rows),
competencies unique to each side, shared competencies with level differences, and
responsibilities side by side. Useful for grading reviews, merge decisions on
duplicates, and promotion readiness talks.

## AI Assistant (standalone)
For work not tied to a stored profile: generate a complete profile from a title,
convert a pasted JD into the Irancell structure, estimate a grade with evidence,
recommend KPIs/qualifications, improve writing, translate. The result badge tells you
whether the answer came from the generative provider or corpus mining.

## Import / Export (HR)
- **Import master workbook** — refreshes all profiles from the bundled master file;
  safe to repeat (updates, never duplicates).
- **Bulk upload** — download the blank template, fill rows, upload; the result banner
  shows created/updated/skipped counts.
- **Export all to Excel** — full library or filtered (e.g. Published only).

## Administration (admin)
Duplicate scan (merge candidates with similarity %), review housekeeping scan
(review-due & expired notifications), audit log of every change, backup guidance.
