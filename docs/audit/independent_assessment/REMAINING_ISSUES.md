# Scholar Lens — Remaining Issues & Technical Debt Register

**Document Version:** 1.0.0  
**Audit Date:** November 6, 2026  
**Auditor:** Independent Principal Software Auditor & QA Architect  

---

## 1. Executive Summary

This register enumerates all verified defects, architectural mismatches, and operational tasks identified during the forensic audit of the Scholar Lens repository.

---

## 2. Itemized Issue Register

### Issue 1: Route Path Mismatches in `static/js/api_client.js`
- **Severity:** High (Frontend Client Defect)
- **Component:** `static/js/api_client.js`
- **Description:**  
  Several methods in `api_client.js` target endpoint paths that do not match the backend URL definitions in `scholar_lens/api.py`:
  - `getOpportunities()` calls `GET /api/opportunities/` $\implies$ Backend defines `GET /api/openings/` (Returns 404).
  - `getFundingCalls()` calls `GET /api/funding/` $\implies$ Backend defines `GET /api/funding-calls/` (Returns 404).
  - `getAnalyticsOverview()` calls `GET /api/analytics/overview/` $\implies$ Backend defines `GET /api/analytics/research/` (Returns 404).
  - Detail lookup methods (`getResearcher(id)`, `getPublication(id)`, `getFacility(id)`, `getFundingCall(id)`) call `/api/<resource>/<id>/`, but `scholar_lens/api.py` only defines collection endpoints with query filters.
  - Endpoints `GET /api/bookings/` and `GET /api/projects/` were omitted from `api_client.js`.
- **Recommended Remediation:**  
  Update `static/js/api_client.js` to align method URLs exactly with `scholar_lens/api.py` and implement handlers for `/api/bookings/` and `/api/projects/`.

---

### Issue 2: Frontend Server-Side Rendering vs. Asynchronous API Utilization
- **Severity:** Medium (Architectural Decoupling)
- **Component:** Django Templates (`templates/papers/list.html`, `templates/facilities/list.html`, etc.)
- **Description:**  
  The application views are almost entirely server-rendered (Django views querying ORM models and passing QuerySets into context). `static/js/api_client.js` is loaded globally via `base.html`, but no template scripts actively invoke `ScholarLensAPI` methods to fetch or mutate data asynchronously.
- **Recommended Remediation:**  
  Connect interactive filter chips and real-time search inputs in `papers/list.html` and `researchers/list.html` to `ScholarLensAPI.bindLiveExpertiseSearch` and `ScholarLensAPI.getPublications`.

---

### Issue 3: Unapplied Migrations on Main PostgreSQL Database
- **Severity:** Medium (Operational Task)
- **Component:** Primary Database `scholar_lens`
- **Description:**  
  While the Django test runner (`manage.py test`) automatically applies all 29 migrations to the transient test database (`test_scholar_lens`), `python manage.py showmigrations` reveals that all 29 migrations are unapplied on the primary database `scholar_lens`.
- **Recommended Remediation:**  
  Execute `python manage.py migrate` against the main PostgreSQL database instance before starting the live application server.

---

### Issue 4: Google OAuth Live Credentials and Production Domain Registration
- **Severity:** Medium (Operational / Cloud Configuration)
- **Component:** `accounts/google_auth.py`, `.env`
- **Description:**  
  Google OAuth is unit and integration tested with mocks, and the redirect URI generation supports dynamic host resolution and HTTPS reverse proxies. However, live Google Single Sign-On requires client credentials from Google Cloud Console and domain verification for the target production host (e.g. `https://scholar-lenss.vercel.app`).
- **Recommended Remediation:**  
  Create OAuth credentials in Google Cloud Console, add `https://<production-domain>/accounts/google/callback/` to Authorized Redirect URIs, and supply `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` via production environment variables.

---

### Issue 5: Cypress E2E Test Suite Not Executed
- **Severity:** Low (Test Verification Gap)
- **Component:** `cypress/e2e/` (13 specifications)
- **Description:**  
  The 13 Cypress E2E specifications were not executed during the automated test runs because they require a dedicated live web server running on port 8001 with pre-populated seed data.
- **Recommended Remediation:**  
  Set up a continuous integration (CI) workflow that launches `python manage.py runserver 127.0.0.1:8001` with seed fixtures and runs `npx cypress run`.

---

### Issue 6: Monolithic Stylesheet Maintenance (`style.css`)
- **Severity:** Low (Code Maintainability)
- **Component:** `static/css/style.css`
- **Description:**  
  `style.css` is a monolithic file of 2,446 lines. While neo-brutalist properties were neutralized, legacy classes for complex 3D book parallax keyframes and tilts remain present.
- **Recommended Remediation:**  
  Break down `style.css` into modular SCSS components (`_tokens.scss`, `_layout.scss`, `_components.scss`) or migrate fully to the utility-based `institutional_tokens.css`.
