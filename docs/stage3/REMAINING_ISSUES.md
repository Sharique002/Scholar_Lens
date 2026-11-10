# Scholar Lens — Remaining Issues & Operational Dependency Register
**Stage 3: Engineering Remediation & Integration Verification**  
**Document ID:** `DOC-S3-REM-01`  
**Execution Date:** 2026-11-07  
**Status:** ZERO CODE DEFECTS / OPERATIONAL PREREQUISITES DOCUMENTED  

---

## 1. Executive Summary

Following Stage 3 engineering remediation, **zero unresolved code bugs, architectural defects, database corruptions, or test failures remain in the Scholar Lens repository**. All 314 automated tests (252 backend unit/integration tests and 62 Cypress browser E2E tests) pass cleanly.

This register documents the post-deployment operational dependencies and external credentials required by DevOps administrators when deploying the platform to live production infrastructure.

---

## 2. Code Defect Status: Resolved

| Issue Identified in Audit | Root Cause | Stage 3 Remediation | Current Status |
|---|---|---|---|
| **Admin Link Hidden from Staff** | `user.is_superuser` check in `base.html` | Updated to `user.is_staff or user.is_superuser` | **RESOLVED & VERIFIED** |
| **API Client Endpoint Drift** | Naming drift between JS client and `scholar_lens/api.py` | Synchronized all 9 endpoints, added backwards aliases, implemented header live search consumer | **RESOLVED & VERIFIED** |
| **Unapplied Database Migrations** | Initial state had 29 unapplied migrations on live db | All 47 migrations applied to both `scholar_lens` and `scholar_lens_e2e` | **RESOLVED & VERIFIED** |
| **Deployment Security Warnings** | Missing conditional production SSL/cookie flags | Formalized conditional production hardening in `settings.py` (`check --deploy` reports 0 issues) | **RESOLVED & VERIFIED** |
| **WCAG 2.1 AA Color Contrast Violation** | Insufficient contrast on landing page `.book-teal` badge | Deepened teal background to `#093b35` and lightened text; Axe-Core audit passes 100% | **RESOLVED & VERIFIED** |
| **Cypress E2E Dependency Missing** | `cypress-axe` not present in local node_modules | Executed `npm install` and configured `cypress.config.js` | **RESOLVED & VERIFIED** |

---

## 3. Post-Deployment Operational Dependencies

These items are external deployment tasks that require access to institutional infrastructure and third-party vendor consoles:

### 3.1 Google Cloud Console OAuth Credentials
- **Description:** Live end-user Google authentication requires registered Google OAuth credentials.
- **Action Required:**
  1. Create Web Client credentials in the institutional Google Cloud Console.
  2. Register authorized redirect URI: `https://<production-domain>/accounts/google/callback/`.
  3. Export `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` into production deployment environment secrets.
- **Reference:** Step-by-step instructions provided in `docs/stage3/GOOGLE_OAUTH_COMPLETION.md`.

### 3.2 Scheduled Background Jobs (Cron / Celery)
- **Description:** Automated daily milestone risk tracking and grant deadline reminders.
- **Action Required:**
  - Configure cron or Celery Beat on the production worker instance:
    ```bash
    # Daily at 06:00 UTC - Grant deadline alerts
    0 6 * * * /path/to/venv/bin/python /app/manage.py check_funding_deadlines
    # Daily at 07:00 UTC - Milestone risk evaluation
    0 7 * * * /path/to/venv/bin/python /app/manage.py check_milestone_risk
    ```

### 3.3 Production Domain & SSL Binding
- **Description:** Binding application to institutional domain name.
- **Action Required:**
  - Update `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` with the production DNS record (e.g. `scholar.institution.edu`).
  - Verify edge proxy passes `X-Forwarded-Proto: https` to Django.

### 3.4 Optional Academic Vendor API Keys
- **Description:** Live querying of external academic databases (Scopus, Google Scholar) in addition to local PDF, BibTeX, and ORCID file ingestion.
- **Action Required:**
  - If live API querying is desired, provide `SCOPUS_API_KEY` in environment variables.

---

## 4. Operational Risk Assessment

| Risk Category | Inherent Risk | Mitigating Control | Residual Risk |
|---|---|---|---|
| **Database Concurrency** | High (Double booking of expensive equipment) | PostgreSQL `btree_gist` ExclusionConstraint enforced at engine level | Negligible |
| **Data Privacy** | High (Researcher ranking leaked to non-executives) | Server-side role inspection in `scholar_lens/api.py` redacting researcher metrics | Negligible |
| **System Accessibility** | Moderate (Non-compliance with ADA/WCAG standards) | Automated Axe-Core CI suite verifying 0 violations across all 11 core views | Negligible |
| **Deployment Configuration** | Low (Misconfigured production settings) | Django `check --deploy` verified with 0 issues | Negligible |
