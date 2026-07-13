# Executive Summary & Product Vision

## Executive summary

MTN Irancell's job profiles have historically lived in ~1,450 individual Word documents,
flattened into a master Excel workbook for oversight. That model creates the problems the
organization already feels: near-duplicate profiles, titles cut off in transcription,
profiles unreviewed for years (average review age ≈ 3.8 years at import), no linkage to
career paths or competency analytics, and a signoff process tracked on paper.

The **Job Profile Management System (JPMS)** replaces documents with a governed master
record. Every profile keeps the exact structure of the official Irancell template — the
same sections, the same signoff chain (Line Manager / Functional Manager / OA / HoD /
CHRO / CEO-COO), the same level structure (1, 2, 2H, 3, 3H, 4, 5), the same Live Y'ello
behavioral values — but becomes structured, versioned, searchable data with a full
approval workflow and AI assistance.

At go-live the system already contains the organization's entire current library:
1,446 profiles across 30 divisions, ~1,240 distinct competencies with required levels,
15,500 responsibility statements, and auto-derived career ladders within job families.

**Business outcomes**

1. **One authoritative record per role** — recruitment, performance, learning,
   compensation and succession all read the same profile.
2. **Governance by construction** — profiles cannot be published without passing the
   review chain; every change is versioned and audited.
3. **Analytics HR never had** — grade distributions, family × level heat maps,
   competency coverage, outdated-profile counts, duplicate detection.
4. **10× faster profile authoring** — new profiles start from AI drafts grounded in the
   organization's own similar roles, not blank pages.

## Product vision

*The job profile becomes the connective tissue of the HR ecosystem.* Recruiters open a
vacancy against a published profile. Learning paths derive from its competency gaps.
Succession slates come from its career-path graph. Compensation reviews read its grade
and authority matrix. Employees see, for any role in the company, what it does, what it
requires, and how to get there.

### Design philosophy

Think Microsoft 365 / Workday / SAP Fiori / Notion: one clean shell, a sidebar of five
destinations, everything reachable in ≤ 2 clicks, search everywhere, no training
required for HR users. Enterprise depth (workflow, RBAC, audit, integrations) stays
behind the scenes until needed.

### Non-goals (v1)

- Payroll/compensation calculation (integration target, not a feature)
- Position budgeting and headcount planning (reads profiles; lives in workforce planning)
- Replacing the HRIS employee master (JPMS links employees to profiles; HRIS owns people data)
