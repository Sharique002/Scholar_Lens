# Scholar Lens — Stage 7.2.2: Regression Evidence & Test Count Reconciliation

**Document ID:** `SL-STAGE7-2-2-TEST-RECON-001`  
**Date:** 2026-11-12  
**Scope:** Test Discovery Reconciliation, Non-Overlapping Cardinality Audit, and Execution Telemetry  
**Author:** AI Quality Assurance & Verification Specialist  

---

## 1. Executive Summary

This report establishes the exact mathematical and empirical reconciliation of all automated test suites across Scholar Lens. In previous documentation, individual sub-suites (such as the 14 storage tests and 14 Google OAuth tests) were occasionally cited alongside the aggregate 266 Django tests without clarifying their subset relationship.

**Definitive Clarification:**
1. The **14 persistent storage & security tests** (`tests/test_storage.py`) are **STRICTLY INCLUDED WITHIN** the 266 Django tests discovered by the Django test runner (`manage.py test tests`). They are **NOT** additional tests.
2. The **14 Google OAuth tests** (`tests/test_google_auth.py`) are likewise **STRICTLY INCLUDED WITHIN** the 266 Django tests.
3. The **66 Cypress scenarios** run in a separate JavaScript/Node.js browser automation runtime across 13 specification files and are **NOT** part of the Python/Django test runner.
4. The **true non-overlapping test total** across the entire platform is **266 Django automated tests + 66 Cypress E2E scenarios = 332 verified test cases**.

---

## 2. Complete File-by-File Django Test Suite Reconciliation

Discovery Command: `python manage.py test tests` (executing all `test_*.py` files in `tests/`).

| File Name | Test Class / Scope | Exact Discovered Tests | Cumulative Count | Subset Relationship |
|---|---|---|---|---|
| `test_advanced_hardening.py` | Rate limiting, SQL injection, XSS, CSP | **22** | 22 | Security Baseline |
| `test_analytics.py` | Departmental metrics & analytics APIs | **4** | 26 | Institutional Workflows |
| `test_authors.py` | Author disambiguation & profile matching | **3** | 29 | Research Office Hub |
| `test_dedup.py` | Paper deduplication & similarity matching | **5** | 34 | Research Office Hub |
| `test_expertise_search.py` | Full-text PostgreSQL search vector | **3** | 37 | Institutional Discovery |
| `test_facilities.py` | Equipment bookings & exclusion constraints | **19** | 56 | Facility Management |
| `test_funding.py` | Grants, calls, and application lifecycles | **14** | 70 | Research Office Hub |
| `test_google_auth.py` | **Google OAuth 2.0 / OIDC Authentication** | **14** | **84** | **Sub-suite (14 tests)** |
| `test_google_scholar_integration.py` | Scopus/Scholar synchronization & ingestion | **14** | 98 | External Ingestion |
| `test_import.py` | BibTeX, RIS, and CSV batch import | **4** | 102 | Ingestion Engine |
| `test_milestones.py` | Project deliverables & progress tracking | **21** | 123 | Project Management |
| `test_office.py` | Research office executive summaries | **3** | 126 | Executive Reporting |
| `test_opportunities.py` | Research opening creation & applications | **5** | 131 | Student Opportunities |
| `test_p08_gaps.py` | P08 boundary conditions & calendar export | **10** | 141 | P08 Core Modules |
| `test_profiles.py` | Researcher profile editing & verification | **6** | 147 | Institutional Profiles |
| `test_publications.py` | Citation tracking & publication metadata | **7** | 154 | Publication Engine |
| `test_scholar_lens.py` | Comprehensive application integration suite | **85** | 239 | Core System Workflows |
| `test_storage.py` | **Cloudflare R2 Storage & Privacy Controls** | **14** | **253** | **Sub-suite (14 tests)** |
| `test_suggestions.py` | Collaboration network suggestion engine | **6** | 259 | Network Analysis |
| `test_ums_shell.py` | University Management System navigation | **7** | **266** | Shell & Navigation |

**Total Unique Django Python Tests Discovered & Executed:** **266 Tests (100% Non-Overlapping)**

---

## 3. Persistent Storage Sub-Suite Breakdown (`tests/test_storage.py`)

The 14 storage tests in `tests/test_storage.py` comprise three distinct functional categories:

| Category | Method Name | Verification Purpose |
|---|---|---|
| **Unit Tests (7)** | `test_default_storage_is_filesystem_when_r2_disabled` | Proves fallback to `FileSystemStorage` when R2 is disabled. |
| | `test_r2_storage_attributes_and_acls` | Proves `default_acl=None`, `signature_version=s3v4`, `region_name=auto`. |
| | `test_r2_public_media_storage_attributes` | Proves public media storage disables querystring auth tokens. |
| | `test_r2_presigned_url_generation` | Proves presigned URL generation with `X-Amz-Signature`. |
| | `test_r2_upload_and_save` | Proves `_save()` invokes S3 PUT without overwriting files. |
| | `test_r2_delete` | Proves `delete()` cleanly dispatches to S3 DELETE. |
| | `test_r2_storage_url_failure_handling` | Proves connection failures are caught, logged, and handled gracefully. |
| **Security Tests (4)** | `test_cv_access_restricted_to_faculty_owner` | Proves confidential CV URLs are hidden from unauthenticated & peer students. |
| | `test_presigned_url_expiry_defaults_and_overrides` | Proves presigned URLs expire strictly in 3600 seconds (1 hour). |
| | `test_r2_private_bucket_default_acl_none` | Proves private bucket default policy prevents accidental public access. |
| | `test_storage_logger_does_not_leak_secrets_on_error` | Proves error logging never dumps AWS credentials or auth headers. |
| **Integration Tests (3)**| `test_cv_upload_validation_preserved` | Proves `%PDF-` header check and 5 MB size limit rejection. |
| | `test_paper_download_remote_storage_redirect` | Proves `paper_download` view catches `NotImplementedError` and redirects. |
| | `test_ai_extract_text_remote_storage_stream_support` | Proves PyMuPDF extracts abstract text from remote streams via `open('rb')`. |

**Total in `tests/test_storage.py`:** **14 Tests** (Integrated directly into the 266-test suite).

---

## 4. Cypress End-to-End Suite Reconciliation (`cypress/e2e/`)

Discovery Command: `npx cypress run` across all spec files in `cypress/e2e/`.

| Spec File | Functional Domain | Exact Scenarios (`it` blocks) |
|---|---|---|
| `01_shell.cy.js` | Top navbar, navigation drawer, authentication toggles | **9** |
| `02_mobile.cy.js` | Responsive mobile viewport layouts & hamburger menu | **3** |
| `03_dashboard.cy.js` | Researcher dashboard metrics & recent activities | **3** |
| `04_facilities.cy.js` | Facility directory, equipment booking workflows | **8** |
| `05_funding.cy.js` | Funding calls, grant application submissions | **4** |
| `06_milestones.cy.js` | Project milestone creation, progress updates | **4** |
| `07_profiles.cy.js` | Public researcher profile views & bio updates | **3** |
| `08_publications.cy.js` | Publication search, citation count badges | **3** |
| `09_expertise_search.cy.js` | Institutional expertise search & keyword filters | **4** |
| `10_collaboration.cy.js` | Collaboration suggestions & network graphs | **4** |
| `11_openings.cy.js` | Research openings list, detail view, application modal | **5** |
| `12_reports.cy.js` | Evaluation reports & departmental analytics export | **5** |
| `13_accessibility.cy.js` | WCAG 2.1 AA accessibility checks & keyboard navigation | **11** |

**Total Unique Cypress E2E Scenarios:** **66 Scenarios across 13 Specifications**

---

## 5. Non-Overlapping Grand Total Summary

```text
+-------------------------------------------------------------------+
|                     SCHOLAR LENS TEST SUITE                      |
+-------------------------------------------------------------------+
|  1. Django Automated Suite (PostgreSQL 16)         : 266 tests    |
|     ├── Core & Domain Modules (18 test files)      : 238 tests    |
|     ├── Persistent Storage & Security              :  14 tests    |
|     └── Google OAuth 2.0 / OIDC                    :  14 tests    |
|                                                                   |
|  2. Cypress End-to-End Browser Suite (Electron/Node) :  66 tests  |
|     └── UI Scenarios across 13 Specifications                     |
+-------------------------------------------------------------------+
|  GRAND TOTAL (Non-Overlapping Verified Tests)       : 332 tests   |
+-------------------------------------------------------------------+
```

Zero overlapping test counts were combined to inflate numbers. All 266 Python tests execute in Django, and all 66 Cypress scenarios execute in Cypress.
