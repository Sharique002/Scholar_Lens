# Scholar Lens — Baseline Test & Verification Report

**Document Version:** 1.0.0  
**Audit Date:** November 6, 2026  
**Auditor:** Principal Software Architect & QA Automation Lead  
**Execution Environment:** Windows 11 Host, Python 3.11.9, Django 4.2.27, PostgreSQL 16.15 (Port 5433 via WSL2 Ubuntu 24.04), Node.js v24.14.0, npm 11.9.0  

---

## 1. Executive Summary

A comprehensive automated baseline evaluation of the entire Scholar Lens platform was performed using the active PostgreSQL database engine.

The platform successfully executed **all 252 automated unit and integration tests** with **zero failures and zero errors**.

| Metric | Measured Baseline Value | Target Threshold | Compliance Status |
|---|---|---|---|
| **Django System Check** | 0 errors, 0 warnings (0 silenced) | 0 issues | **PASS** |
| **Total Test Suite** | 252 tests executed in 648.4s | 100% Pass Rate | **PASS (252 / 252 OK)** |
| **Database Migrations** | 29 migrations applied cleanly | Consistent Schema | **PASS** |
| **Deduplication Accuracy (M2)** | **96.7%** on 120 test pairs | $\ge 95.0\%$ | **PASS (Surpasses Target)** |
| **Expertise Search Speed (M3)** | **0.042s** across 2,000 profiles | $< 1.0\text{s}$ | **PASS (Surpasses Target)** |
| **Facility Concurrency (M6)** | PostgreSQL GiST Exclusion constraint | Zero Overlaps | **PASS** |
| **Dean Privacy Isolation (M9)** | Confidential metrics redacted for non-Dean | 100% Redaction | **PASS** |

---

## 2. Django System Check Verification

Execution Command:
```powershell
python manage.py check
```

Output:
```text
System check identified no issues (0 silenced).
```

- Verified model definition integrity across all 13 Django applications (`accounts`, `researchers`, `papers`, `projects`, `collaboration`, `ai_engine`, `evaluation`, `search`, `dashboard`, `facilities`, `funding`, `opportunities`, `analytics`).
- Verified URL routing patterns, view imports, form configurations, and template context processors.

---

## 3. Database & Migration Audit

Execution Environment:
- **Database Engine:** PostgreSQL 16.15 on `127.0.0.1:5433`
- **Extensions Installed & Verified:** `plpgsql`, `btree_gist`, `pg_trgm`

Migration Status (`python manage.py showmigrations`):
- `accounts`: 2 migrations (`0001_initial`, `0002_userprofile_google_sub`)
- `ai_engine`: 1 migration (`0001_initial`)
- `analytics`: 0 migrations (pure query / aggregation engine)
- `collaboration`: 2 migrations (`0001_initial`, `0002_collaborationsuggestion`)
- `dashboard`: 3 migrations (`0001_initial`, `0002_alter_researchactivity_activity_type`, `0003_alter_researchactivity_activity_type_auditentry`)
- `evaluation`: 3 migrations (`0001_initial`, `0002_evaluationreport_confidence_and_more`, `0003_alter_evaluationreport_options`)
- `facilities`: 1 migration (`0001_initial`)
- `funding`: 2 migrations (`0001_initial`, `0002_fundingapplication`)
- `opportunities`: 2 migrations (`0001_initial`, `0002_alter_opportunityapplication_status`)
- `papers`: 8 migrations (`0001_initial` through `0008_alter_importrun_source`)
- `projects`: 2 migrations (`0001_initial`, `0002_milestone_milestone_progress_lte_100`)
- `researchers`: 3 migrations (`0001_initial`, `0002_department_researcherprofile_scopus_id_and_more`, `0003_researcherprofile_search_document_and_more`)
- `search`: 0 migrations (uses `researchers` and `papers` search fields)

Total Migrations: **29 migrations** applied cleanly without circular dependencies or unapplied operations.

---

## 4. Test Suite Execution Breakdown by Module

Execution Command:
```powershell
$env:DATABASE_URL="postgres://scholar_lens:scholar_lens@127.0.0.1:5433/scholar_lens"; python manage.py test
```

Summary:
```text
Ran 252 tests in 648.434s
OK
Destroying test database for alias 'default'...
```

### Breakdown by Test File:

1. `tests/test_facilities.py` (19 tests):
   - Model string representations and duration properties.
   - Partial overlap rejection via PostgreSQL `ExclusionConstraint` (IntegrityError raised).
   - Back-to-back booking permission (allowed without conflict).
   - Multi-threaded concurrent booking race conditions (zero overlaps allowed).
   - Custodian approval workflow and utilization reporting.
   - Status: **19 / 19 PASSED**

2. `tests/test_dedup.py` (12 tests):
   - Exact DOI deduplication.
   - Normalized Unicode title matching.
   - Benchmark evaluation on `tests/fixtures/dedup_pairs.json` (120 labelled pairs) demonstrating **96.7% accuracy** (acceptance threshold $\ge 95\%$).
   - Short generic titles ($< 4$ words) routed to manual review queue without auto-merging.
   - Idempotent soft-merge undo (`unmerge_paper`).
   - Status: **12 / 12 PASSED**

3. `tests/test_expertise_search.py` (8 tests):
   - Full-text search with pre-computed weighted `SearchVectorField`.
   - Faceted filtering by department and collaboration availability.
   - Sub-second performance benchmark: **0.042 seconds** over 2,000 synthesized researcher profiles.
   - Status: **8 / 8 PASSED**

4. `tests/test_profiles.py` (14 tests):
   - ISO 7064 MOD 11-2 ORCID checksum validation (synthetic ORCIDs rejected).
   - Taxonomy parent-child category assignment.
   - State machine verification (`UNVERIFIED` $\to$ `PENDING` $\to$ `VERIFIED`).
   - Auto-reset of verification on core profile edits.
   - Status: **14 / 14 PASSED**

5. `tests/test_authors.py` (11 tests):
   - Author name variant disambiguation ("R. Kumar", "Kumar, Rajesh", "Rajesh Kumar").
   - Cross-department ambiguous author routing to review queue.
   - Status: **11 / 11 PASSED**

6. `tests/test_import.py` (14 tests):
   - Resilient ORCID and Crossref ingestion.
   - Malformed external record handling (skips missing titles, bad years, HTML tags without failure).
   - Scopus unconfigured credential error handling.
   - Status: **14 / 14 PASSED**

7. `tests/test_suggestions.py` (10 tests):
   - Dual-factor collaboration scoring algorithm.
   - Co-authorship gap bonus (+30 points).
   - Cytoscape.js JSON payload generation and accessible HTML table rendering.
   - Status: **10 / 10 PASSED**

8. `tests/test_opportunities.py` (12 tests):
   - Research opening creation and publishing.
   - PDF application submission and size validation ($\le 5\text{MB}$).
   - Application review queue and automatic project membership enrollment upon acceptance.
   - Status: **12 / 12 PASSED**

9. `tests/test_funding.py` (14 tests):
   - Funding call lifecycle and deadline tracking.
   - Scheduled alert notifications command (`send_funding_alerts` at 14, 7, 1 days).
   - Internal proposal tracking and decision audit logging.
   - Status: **14 / 14 PASSED**

10. `tests/test_milestones.py` (16 tests):
    - Project milestone creation and progress updates.
    - Depth-First Search (DFS) circular dependency prevention.
    - Nightly risk detection management command (`check_milestone_risk`).
    - At-risk projects board.
    - Status: **16 / 16 PASSED**

11. `tests/test_analytics.py` (15 tests):
    - Strict July 1 - June 30 academic-year metrics computation.
    - Departmental productivity rollups.
    - **Dean confidential privacy:** Individual researcher productivity strictly redacted for non-Dean viewers.
    - Status: **15 / 15 PASSED**

12. `tests/test_office.py` (12 tests):
    - Research Office command center consolidating verification, deduplication, author, and risk queues.
    - Immutable tamper-resistant `AuditEntry` recording.
    - Status: **12 / 12 PASSED**

13. `tests/test_google_auth.py` (8 tests):
    - Google OAuth2 Authorization Code Flow.
    - State token validation and CSRF mitigation.
    - Cryptographic ID token claims verification (`iss`, `aud`, `exp`, `email_verified`).
    - Account provisioning and Google `sub` binding.
    - Status: **8 / 8 PASSED**

14. `tests/test_google_scholar_integration.py` (6 tests):
    - SerpAPI scholar synchronization with open fallback search.
    - Trend analysis and marquee research announcements.
    - Status: **6 / 6 PASSED**

15. `tests/test_p08_gaps.py` (18 tests):
    - The 9 P08 JSON API endpoints (`/api/researchers/`, `/api/publications/`, `/api/search/expertise/`, etc.).
    - Session authentication enforcement (`401 JSON` when unauthenticated).
    - RFC 5545 iCalendar (`.ics`) export.
    - Status: **18 / 18 PASSED**

16. `tests/test_ums_shell.py` (15 tests):
    - University navigation shell, 9 core sidebar items, responsive layout.
    - Notification feed and read tracking.
    - Status: **15 / 15 PASSED**

17. `tests/test_advanced_hardening.py` (10 tests):
    - Edge cases, transaction rollbacks, SQL injection prevention, XSS escaping in templates.
    - Status: **10 / 10 PASSED**

18. `tests/test_scholar_lens.py` (38 tests):
    - Core system test cases covering accounts, papers, search, projects, AI services, and 7-dimension evaluation engine.
    - Status: **38 / 38 PASSED**

---

## 5. End-to-End Cypress Test Environment

Configuration & Dependencies:
- **Specification Files:** 13 specifications located in `cypress/e2e/`:
  - `01_shell.cy.js`: Application shell, top navigation, sidebar, branding.
  - `02_mobile.cy.js`: Responsive viewport behavior on mobile viewports.
  - `03_dashboard.cy.js`: Quick actions, metrics strip, activity feed.
  - `04_facilities.cy.js`: Directory, booking workflow, conflict rejection.
  - `05_funding.cy.js`: Funding calls, alert subscription, proposals.
  - `06_milestones.cy.js`: Milestone delivery, cycle checks, risk board.
  - `07_profiles.cy.js`: Taxonomy selector, ORCID validation, verification queue.
  - `08_publications.cy.js`: Ingestion, deduplication review queue, merge/unmerge.
  - `09_expertise_search.cy.js`: Ranked search, faceted filters, performance.
  - `10_collaboration.cy.js`: Suggestions, request flow, Cytoscape graph.
  - `11_openings.cy.js`: Openings board, PDF application, candidate enrollment.
  - `12_reports.cy.js`: Academic year report, Dean confidential privacy, CSV download.
  - `13_accessibility.cy.js`: Axe-core automated WCAG 2.1 AA accessibility audit.
- **Node & NPM:** Node.js v24.14.0, npm 11.9.0 available on host. `package.json` contains Cypress 13.15.0 and `cypress-axe`.

---

## 6. Baseline Verification Conclusions

1. **Backend & Data Layer:** The Django backend is robust, strictly compliant with P08 requirements, and backed by a 100% passing automated test suite on PostgreSQL 16.
2. **Primary Stabilization Target:** The primary defects and vulnerabilities lie in:
   - The frontend presentation layer (conflicting neo-brutalist CSS vs LPU institutional UMS styling).
   - Inconsistent context processor variables for role-based navigation (`is_dean` / `is_office`).
   - Clean production configuration for Google OAuth redirect URIs and reverse proxies.
   - Centralized frontend client consumption of the documented P08 APIs.
