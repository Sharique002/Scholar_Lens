# Scholar Lens — Complete Research Intelligence & Collaboration Hub (P08)

## 1. Architectural Overview
Scholar Lens is a unified institutional research intelligence portal built with Python 3.11, Django 4.2, and PostgreSQL 15. The system integrates nine distinct academic intelligence modules into an institutional university portal inspired by the LPU UMS design system.

### Core Institutional Design Tokens
- **Primary Maroon:** `#9B2335`
- **Dark Maroon:** `#7A1B29`
- **Maroon Tint:** `#FBEFF1`
- **Primary Action Orange:** `#F37021`
- **Text Ink:** `#1F2328`
- **Muted Text:** `#5B6270`
- **Border Neutral:** `#E2E4E8`
- **Page Background:** `#F5F5F7`

---

## 2. P08 Module Implementations

### M1: Researcher & Expertise Profiles
- **Taxonomy Hierarchy:** Parent-child self-referential categories in `ResearchInterest` for faceted discovery.
- **ORCID Checksum Validation:** Strict ISO 7064 MOD 11-2 validation algorithm ensuring synthetic or invalid ORCID IDs cannot be registered.
- **Verification Workflow:** States `UNVERIFIED`, `PENDING`, `VERIFIED`, and `REJECTED`. Core profile changes automatically reset verification to `PENDING` or `UNVERIFIED`.
- **Audit Logging:** Every verification decision is permanently recorded in `AuditEntry`.

### M2: Publication Register & Deduplication
- **Multi-Tier Deduplication:** 1) Exact DOI match, 2) NFKD Unicode title normalisation, 3) PostgreSQL GIN trigram candidate scan, and 4) RapidFuzz Token Sort Ratio fuzzy scoring.
- **Soft Merge Architecture:** `merged_into` self-foreign key with `ActivePaperManager` (`merged_into__isnull=True`) ensuring deduplicated papers are cleanly hidden while preserving full citation provenance.
- **External Ingestion:** Resilient ORCID and Crossref ingestion commands that skip malformed records without failing.
- **Author Disambiguation:** Confidence thresholding (`AUTHOR_AUTO_MATCH = 92%`, `AUTHOR_REVIEW_MIN = 80%`) routing ambiguous matches to the institutional author review queue.

### M3: Expertise Discovery & Hybrid Search
- **Stored Search Vector:** Pre-computed `SearchVectorField` on `ResearcherProfile` weighted by importance:
  - Weight A: Research Interests & Skills
  - Weight B: Headline, Department, and Department Code
  - Weight C: Biography and Institutional Affiliation
  - Weight D: Confirmed Authored Paper Titles
- **Faceted Search:** Real-time faceting by department, collaboration availability, and top skills.
- **Performance Benchmark:** Full-text ranked queries execute in `< 1.0s` across 2,000+ researcher profiles.

### M4: Research Opportunities Board
- **Openings Management:** Departmental and project-linked openings specifying required skills, open spots, and application deadlines.
- **Application Submission:** Validates PDF uploads strictly ($\le 5\text{MB}$, application/pdf mime type).
- **Review Queue:** Project leaders and faculty review applications, with acceptance automatically enrolling candidates into project membership.

### M5: Collaboration Identification & Graph
- **Algorithmic Suggestion Engine:** Dual-factor scoring combining expertise adjacency (shared interests, parent taxonomy categories, complementary skills, cross-department bonus) and co-authorship gap bonus (+30 points if researchers have never co-authored a paper or shared a project).
- **Interactive Network Graph:** Cytoscape.js 3.28.1 loaded strictly on the graph page to visualize institutional collaboration links and suggested pairings.
- **Accessibility Fallback:** Complete tabular HTML representation for screen readers and search engines.

### M6: Research Facilities & Equipment Catalogue
- **PostgreSQL ExclusionConstraint:** Prevents double-booking at the database engine level using `gist` index on `('facility', RangeOperators.EQUAL)` and `('during', RangeOperators.OVERLAPS)`.
- **Weekly Slot Management:** Enforces facility operating hours with database check constraints.
- **Custodian Dashboard:** Custodians approve/reject slot requests and review real-time equipment utilization.

### M7: Funding Call Register
- **Lifecycle Tracking:** Active countdown badges (`Open`, `Closing Soon`, `Closes Today`, `Closed`).
- **Automated Deadline Alerts:** Scheduled management command `send_funding_alerts` triggers notifications at 14, 7, and 1 day before close for watching researchers.
- **Institutional Endorsements:** Tracks internal grant proposals and records awards.

### M8: Project Milestones & Timeline
- **Dependency Cycle Prevention:** Depth-First Search (DFS) validation prevents circular milestone dependency chains.
- **Interactive Visualizations:** Pure CSS/SVG Gantt chart and milestone delivery timelines.
- **Scheduled At-Risk Detection:** Nightly management command flags delayed or overdue milestones on the institutional at-risk board.

### M9: Reporting & Research Office Governance Hub
- **Academic Year Reporting:** Strict July 1 to June 30 reporting windows (e.g., AY 2025–2026).
- **Departmental Productivity:** Aggregates publications count, funding success rate, and facility utilization hours.
- **Dean Confidential Privacy:** Per-researcher individual productivity metrics are strictly restricted to the Dean of Research and redacted for all other viewers.
- **Research Office Hub:** Unified administrative command centre aggregating verification queues, deduplication reviews, author match queues, at-risk milestones, and immutable audit logs.

---

## 3. JSON API (spec section 8)
Read-only, session-authenticated (401 JSON when logged out). `?limit=` caps at 100.

| Endpoint | Notes |
|---|---|
| `GET /api/researchers/` | `?department=<code>` |
| `GET /api/publications/` | Active (non-merged) papers, `?year=` |
| `GET /api/search/expertise/?q=` | Full-text ranked, `?department=<code>` |
| `GET /api/openings/` | Open openings only |
| `GET /api/projects/` | Public + own/member projects (staff see all), with milestones and risk |
| `GET /api/facilities/` | Active facilities with opening hours |
| `GET /api/bookings/` | Own and custodian bookings (staff see all) |
| `GET /api/funding-calls/` | Published calls, `?open=true` |
| `GET /api/analytics/research/?year=` | Office/Dean only; per-researcher metrics Dean only |

## 4. Integrations and notifications added
- **Scopus import:** `python manage.py import_publications --source scopus --scopus-author <id>` or the Import page. Needs `SCOPUS_API_KEY` (Elsevier licence); malformed entries are skipped like ORCID/Crossref.
- **Calendar export:** approved bookings offer an "Add to calendar" `.ics` download (`/facilities/bookings/<id>/calendar.ics`) that Google Calendar and Outlook import.
- **Notifications:** posting an opening alerts researchers whose skills match; a newly computed collaboration suggestion alerts the researcher once (recomputes do not re-notify).
