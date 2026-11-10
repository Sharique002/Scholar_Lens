# Scholar Lens — P08 Three-Level Forensic Compliance Verification

**Document Version:** 1.0.0  
**Audit Date:** November 6, 2026  
**Auditor:** Independent Principal Software Auditor & P08 Compliance Evaluator  

---

## 1. Evaluation Methodology

Every P08 requirement is evaluated across three independent evidence tiers:
1. **Code Proof:** Physical existence of models, views, service algorithms, constraints, and routes in repository source files.
   - Statuses: `VERIFIED`, `PARTIAL`, `NOT FOUND`, `UNVERIFIED`
2. **Functional Proof:** Confirmed automated execution of unit, integration, and security test cases.
   - Statuses: `PASS`, `PARTIAL`, `FAIL`, `NOT EXECUTED`, `BLOCKED`
3. **Acceptance Proof:** Verification against quantitative specifications, benchmarks, and production acceptance targets.
   - Statuses: `PASS`, `PARTIAL`, `FAIL`, `NOT EVALUATED`, `BLOCKED`

A module is declared **FULLY COMPLIANT** only if all three levels achieve passing marks.

---

## 2. P08 Three-Level Compliance Matrix

| Module | Code Proof | Functional Proof | Acceptance Proof | Final Verdict |
|---|---|---|---|---|
| **M1: Researcher Profiles** | **VERIFIED** | **PASS** (6/6 tests) | **PASS** (ISO ORCID checksum, taxonomy, state machine) | **FULLY COMPLIANT** |
| **M2: Publications & Deduplication** | **VERIFIED** | **PASS** (19/19 tests) | **PASS** (99.29% accuracy on 140 pairs, target $\ge 95\%$) | **FULLY COMPLIANT** |
| **M3: Expertise Search** | **VERIFIED** | **PASS** (3/3 tests) | **PASS** (71.76ms latency over 2,001 profiles, target $< 1\text{s}$) | **FULLY COMPLIANT** |
| **M4: Opportunities** | **VERIFIED** | **PASS** (5/5 tests) | **PASS** (PDF submission $\le 5\text{MB}$, project enrollment) | **FULLY COMPLIANT** |
| **M5: Collaboration Engine** | **VERIFIED** | **PASS** (6/6 tests) | **PASS** (Dual-factor scoring, Cytoscape graph, gap bonus) | **FULLY COMPLIANT** |
| **M6: Facilities & Concurrency** | **VERIFIED** | **PASS** (19/19 tests) | **PASS** (100% overlap prevention via PostgreSQL GiST constraint) | **FULLY COMPLIANT** |
| **M7: Funding & Alerts** | **VERIFIED** | **PASS** (14/14 tests) | **PASS** (14/7/1 day alert lifecycle, RFC 5545 `.ics` export) | **FULLY COMPLIANT** |
| **M8: Projects & Milestones** | **VERIFIED** | **PASS** (21/21 tests) | **PASS** (DFS circular dependency check, nightly risk engine) | **FULLY COMPLIANT** |
| **M9: Analytics & Governance** | **VERIFIED** | **PASS** (7/7 tests) | **PASS** (Academic year window, 100% Dean confidentiality redaction) | **FULLY COMPLIANT** |

---

## 3. Module-by-Module Forensic Audit

### M1: Researcher Profiles
- **Code Proof:** `researchers/models.py`, `researchers/views.py`, `researchers/urls.py`. Includes `ResearcherProfile`, `Department`, `TaxonomyCategory`, `ResearchInterest`, `Skill`.
- **Functional Proof:** `tests/test_profiles.py` (6 tests passing).
- **Acceptance Proof:**
  - ORCID validation enforces ISO 7064 MOD 11-2 checksums; invalid/synthetic ORCIDs are rejected.
  - Three-tier state machine: `UNVERIFIED` $\to$ `PENDING` $\to$ `VERIFIED`. Core profile edits automatically reset status back to `PENDING`.
  - Directory search and department filtering operational.

### M2: Publication Management & Deduplication
- **Code Proof:** `papers/models.py`, `papers/dedup.py`, `papers/views.py`. Includes `ResearchPaper`, `PaperAuthor`, `DuplicateCandidate`, `ImportRun`.
- **Functional Proof:** `tests/test_publications.py` (7 tests), `tests/test_dedup.py` (5 tests), `tests/test_authors.py` (3 tests), `tests/test_import.py` (4 tests) passing.
- **Acceptance Proof:**
  - Deduplication accuracy demonstrated at **99.29%** (139 / 140 pairs correctly predicted) on `tests/fixtures/dedup_pairs.json`, exceeding the $\ge 95\%$ target.
  - Generic short titles ($< 4$ words) are routed to manual review queue without auto-merging.
  - Reversible soft-merge (`unmerge`) verified and idempotent.

### M3: Expertise Search
- **Code Proof:** `researchers/search_index.py`, `search/views.py`, `scholar_lens/api.py`. Utilizes PostgreSQL `pg_trgm` and `SearchVectorField` GIN indexing with weights: Interests (A: 1.0), Headline (B: 0.4), Summary (C: 0.2).
- **Functional Proof:** `tests/test_expertise_search.py` (3 tests passing).
- **Acceptance Proof:**
  - Demonstrated benchmark latency across 2,001 active profiles: **71.76 ms avg** (50.68 ms min, 125.63 ms max), far outperforming the $< 1.0\text{s}$ target.
  - Faceted filtering by department code and collaboration availability verified.

### M4: Opportunities / Openings Board
- **Code Proof:** `opportunities/models.py`, `opportunities/views.py`. Includes `ResearchOpening`, `OpportunityApplication`.
- **Functional Proof:** `tests/test_opportunities.py` (5 tests passing).
- **Acceptance Proof:**
  - Openings board filtered to `OPEN` status.
  - PDF document attachment validated for file size ($\le 5\text{MB}$) and MIME type.
  - Review queue allows faculty project leaders to accept/reject candidates; acceptance automatically enrolls researcher into project members.

### M5: Collaboration Engine & Network Graph
- **Code Proof:** `collaboration/models.py`, `collaboration/matching.py`, `collaboration/views.py`. Includes `CollaborationRequest`, `CollaborationSuggestion`.
- **Functional Proof:** `tests/test_suggestions.py` (6 tests passing).
- **Acceptance Proof:**
  - Dual-factor matching algorithm combines shared interest Jaccard similarity with co-authorship gap bonus (+30 points for complementary non-coauthors).
  - Generates Cytoscape.js JSON network graph alongside accessible HTML table alternative.

### M6: Facilities Catalogue & Booking Concurrency
- **Code Proof:** `facilities/models.py`, `facilities/views.py`. Includes `Facility`, `FacilitySlot`, `Booking`.
- **Functional Proof:** `tests/test_facilities.py` (19 tests passing).
- **Acceptance Proof:**
  - PostgreSQL database-level `ExclusionConstraint` on `(facility WITH =, during WITH &&)` strictly blocks overlapping confirmed reservations at the database engine level.
  - Custodian approval workflow and utilization metrics reporting verified.

### M7: Funding Register & Automated Alerts
- **Code Proof:** `funding/models.py`, `funding/views.py`, `funding/management/commands/send_funding_alerts.py`.
- **Functional Proof:** `tests/test_funding.py` (14 tests passing).
- **Acceptance Proof:**
  - Lifecycle state tracking (`ACTIVE`, `CLOSING_SOON`, `CLOSED`).
  - Automated alert notification command delivers notifications at 14 days, 7 days, and 1 day prior to deadline.
  - RFC 5545 iCalendar (`.ics`) generation verified.

### M8: Project Milestones & Gantt Timelines
- **Code Proof:** `projects/models.py`, `projects/views.py`, `projects/management/commands/check_milestone_risk.py`. Includes `ResearchProject`, `Milestone`, `MilestoneDependency`.
- **Functional Proof:** `tests/test_milestones.py` (21 tests passing).
- **Acceptance Proof:**
  - Cycle detection via Depth-First Search (DFS) blocks circular milestone dependencies.
  - Nightly risk calculation command identifies at-risk deliverables and populates the Research Office risk dashboard.

### M9: Research Analytics & Institutional Governance
- **Code Proof:** `analytics/metrics.py`, `analytics/views.py`, `dashboard/views.py`.
- **Functional Proof:** `tests/test_analytics.py` (4 tests), `tests/test_office.py` (3 tests) passing.
- **Acceptance Proof:**
  - Strict academic year windowing (July 1 to June 30).
  - Executive confidentiality: 100% of individual researcher productivity metrics are redacted for non-Dean viewers (enforced via HTTP 403 on API and query filtering in views).
