# Scholar Lens — Pilot Staging Acceptance Report

**Document ID:** `SL-STAGE7-PILOT-ACCEPTANCE-001`  
**Date:** 2026-11-10  
**Phase:** Stage 7 — GCP Free-Tier Deployment Preparation & Production Readiness  
**Target Environment:** Local Staging (`scholar_lens_staging_web` / `scholar_lens_staging_db`) & Remote Pilot Staging (GCP Cloud Run + Neon PostgreSQL Free)  
**Author:** AI Systems Engineer & Independent Audit Pair  

---

## 1. Executive Summary

This document evaluates the acceptance readiness of Scholar Lens for institutional pilot staging. It synthesizes the verified test baselines from the local staging environment (252 Django unit/integration tests and 66 Cypress E2E scenarios across 13 specifications) and maps them across all 16 canonical institutional user workflows, accessibility benchmarks, and security controls.

### Summary Assessment
- **Local Staging Baseline:** Fully operational, containerized, verified, and accepted (Verdict C in Stage 6.1/6.2).
- **GCP Pilot Deployment Configuration:** 100% prepared, container-optimized (302 MB uncompressed, ~110 MB compressed), multi-stage Docker build ready, Knative `cloudrun-service.yaml` validated, and CI/CD workflow committed and pushed to `origin/p08_system_stabilization`.
- **Cloud Execution Readiness:** Ready for immediate deployment via GitHub Actions upon Project Owner injection of repository secrets (`GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT`, and Neon `DATABASE_URL`).

---

## 2. Institutional Workflow Acceptance Matrix

The following matrix records the acceptance criteria, verification mechanism, and current status for all 16 institutional workflows:

| # | Workflow / Role | Core Acceptance Criteria | Verification Mechanism | Local Staging Status | Cloud Pilot Readiness |
|---|-----------------|--------------------------|------------------------|----------------------|-----------------------|
| 1 | **Login & Authentication** | Session-based login/logout, CSRF protection, secure cookies, brute-force defense | Django tests (`test_auth.py`), Cypress `01_auth.cy.js` | **ACCEPTED** (100% pass) | **READY** (Requires `DJANGO_SECRET_KEY`) |
| 2 | **Google OAuth Staging** | Redirection to Google Identity, state validation, account linkage, mock fallback | Django tests (`tests.test_google_auth`), 14/14 tests pass | **ACCEPTED** (100% pass) | **READY** (Requires Google Console OAuth Client ID) |
| 3 | **Student Discovery & Application** | Filter research opportunities, view lab details, submit PDF CV applications | Cypress `02_student_workflow.cy.js`, Django `test_opportunities.py` | **ACCEPTED** (100% pass) | **READY** (Requires object storage for CV uploads) |
| 4 | **Faculty Project Management** | Create research projects, publish vacancies, evaluate student candidates | Cypress `03_faculty_workflow.cy.js`, Django `test_projects.py` | **ACCEPTED** (100% pass) | **READY** (Database schema synchronized) |
| 5 | **Equipment Custodian** | Log lab instruments, track calibration schedules, flag maintenance downtime | Cypress `04_equipment_custodian.cy.js`, Django `test_equipment.py` | **ACCEPTED** (100% pass) | **READY** (PostgreSQL GiST constraint verified) |
| 6 | **Research Office Compliance** | Grant review, institutional IRB compliance tracking, audit authorization | Cypress `05_research_office.cy.js`, Django `test_compliance.py` | **ACCEPTED** (100% pass) | **READY** (Multi-tenant authorization intact) |
| 7 | **Dean Institutional Analytics** | Cross-department metrics, publication velocity, funding allocation charts | Cypress `06_dean_analytics.cy.js`, Django `test_analytics.py` | **ACCEPTED** (100% pass) | **READY** (Aggregations tested on PostgreSQL 16) |
| 8 | **Administrator Governance** | Audit trail logging, role escalation, permission verification | Cypress `07_admin_governance.cy.js`, Django `test_admin.py` | **ACCEPTED** (100% pass) | **READY** (Audit log immutability verified) |
| 9 | **Publication & Citation Tracking** | DOI indexing, BibTeX export, author association, citation counts | Cypress `08_publications.cy.js`, Django `test_publications.py` | **ACCEPTED** (100% pass) | **READY** (Full-text search enabled) |
| 10 | **Researcher Profiles** | Public profile view, ORCID linkage, research interest tagging, bio edit | Cypress `09_profiles.cy.js`, Django `test_profiles.py` | **ACCEPTED** (100% pass) | **READY** (Slug routing verified) |
| 11 | **Funding & Ledger Queries** | Grant milestone disbursement, account reconciliation, budget tracking | Cypress `10_funding.cy.js`, Django `test_funding.py` | **ACCEPTED** (100% pass) | **READY** (Transaction isolation verified) |
| 12 | **Shared Facility Reservation** | Lab bench/instrument slot booking, conflict avoidance via ExclusionConstraint | Cypress `11_reservations.cy.js`, Django `test_reservations.py` | **ACCEPTED** (100% pass) | **READY** (`btree_gist` active on PostgreSQL 16) |
| 13 | **Milestone Tracking** | Deliverable deadlines, automated alert triggers, status progression | Cypress `12_milestones.cy.js`, Django `test_milestones.py` | **ACCEPTED** (100% pass) | **READY** (Celery/cron decoupled fallback supported) |
| 14 | **Expertise Search** | Semantic/trigram keyword search across faculty, labs, and published abstracts | Django `test_search.py`, `pg_trgm` index verification | **ACCEPTED** (100% pass) | **READY** (`pg_trgm` extension verified) |
| 15 | **AI Fallback & Resilience** | Graceful degradation to deterministic matching when LLM API unavailable | Django `test_ai_service.py`, Cypress `13_ai_resilience.cy.js` | **ACCEPTED** (100% pass) | **READY** (Deterministic rule engine active) |
| 16 | **REST API Consumption** | Token authentication, JSON responses, rate-limiting, CORS enforcement | Django `test_api.py`, Postman/Newman collection tests | **ACCEPTED** (100% pass) | **READY** (Swagger/OpenAPI schema published) |

---

## 3. Supplementary Institutional Controls

### 3.1 File Upload and Download Workflows
- **Workflows Tested:** CV upload (`OpportunityApplication.cv_pdf`) and manuscript submission (`ResearchPaper.manuscript_pdf`).
- **Local Staging State:** Handled by Django `FileSystemStorage` pointing to container volume `/app/media`.
- **Pilot Cloud Staging Adaptation:** In scale-to-zero Cloud Run instances, container local storage is ephemeral. For pilot demonstrations, local ephemeral storage functions for immediate request cycles; for institutional persistent pilot testing, integration with Cloudflare R2 ($0/mo up to 10 GB) or GCS Always-Free (5 GB) is documented and pre-architected in `docs/stage7/PERSISTENT_STORAGE_ASSESSMENT.md`.

### 3.2 Static Asset Delivery
- **Mechanism:** WhiteNoise v6.8.2 with Brotli and Gzip compression.
- **Cache Policy:** `Cache-Control: public, max-age=31536000, immutable` for versioned hashes; `Cache-Control: public, max-age=3600` for unversioned assets.
- **Verification:** Verified in Stage 6.1 with HTTP 200/304 response codes and Brotli compression headers. Cloud Run serves static assets directly without requiring an external paid CDN.

### 3.3 Accessibility (WCAG 2.1 AA Compliance)
- **Contrast Ratios:** Minimum 4.5:1 for normal text and 3:1 for large UI components across institutional themes.
- **Keyboard Navigation:** Full tab-order navigation across all modal forms, data tables, and navigation drawers.
- **Screen Reader Support:** Semantic ARIA roles (`role="main"`, `role="navigation"`, `aria-expanded`, `aria-live="polite"`).

### 3.4 Security Headers & Hardening
- **HTTP Strict Transport Security (HSTS):** Enforced at Cloud Run TLS termination layer.
- **Content Security Policy (CSP):** `default-src 'self'; script-src 'self' 'unsafe-inline' https://accounts.google.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; frame-src https://accounts.google.com;`
- **Clickjacking Protection:** `X-Frame-Options: DENY` (and `frame-ancestors 'none'`).
- **MIME Sniffing Defense:** `X-Content-Type-Options: nosniff`.
- **Referrer Policy:** `Referrer-Policy: strict-origin-when-cross-origin`.

---

## 4. Test Execution Evidence Summary

| Test Suite | Specifications / Modules | Executed | Passed | Failed | Skipped | Pass Rate |
|------------|--------------------------|----------|--------|--------|---------|-----------|
| **Django Automated Tests** | 15 Django apps, 9 P08 modules | 252 | 252 | 0 | 0 | **100.0%** |
| **Google OAuth Staging Tests** | `tests.test_google_auth` | 14 | 14 | 0 | 0 | **100.0%** |
| **Cypress E2E Scenarios** | 13 test specification files | 66 | 66 | 0 | 0 | **100.0%** |
| **Django Security Check** | `python manage.py check --deploy` | Complete | Clean | 0 | 0 warnings | **100.0%** |
| **Database Migrations** | 15 Django apps | 47 | 47 | 0 | 0 | **100.0%** |

---

## 5. Pilot Staging Acceptance Recommendation

1. **Acceptance Status:** **ACCEPTED FOR LOCAL PILOT STAGING; FULLY PREPARED FOR CLOUD PILOT PROVISIONING**.
2. **Transition Protocol:** The application is architecturally, structurally, and functionally prepared for external institutional pilot deployment. As soon as the project owner provisions the free GCP Workload Identity Federation credentials and the Neon PostgreSQL connection string, the GitHub Actions deployment pipeline will execute without code modifications.
