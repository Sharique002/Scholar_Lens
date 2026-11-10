# Scholar Lens — Stage 3 Implementation Changelog
**Stage 3: Engineering Remediation & Integration Verification**  
**Document ID:** `DOC-S3-CHG-01`  
**Execution Date:** 2026-11-07  
**Status:** RECORDED & COMMITTED  

---

## 1. Overview

This document records all concrete source code modifications, architectural refinements, bug fixes, configuration enhancements, and database migrations applied during Stage 3 remediation of the Scholar Lens platform.

---

## 2. File-by-File Modification Log

### 2.1 `scholar_lens/settings.py`
- **Category:** Security & Production Deployment
- **Changes:**
  - Added conditional production security controls activated whenever `DEBUG=False`:
    ```python
    if not DEBUG:
        SECURE_SSL_REDIRECT = get_bool_env('SECURE_SSL_REDIRECT', True)
        SESSION_COOKIE_SECURE = get_bool_env('SESSION_COOKIE_SECURE', True)
        CSRF_COOKIE_SECURE = get_bool_env('CSRF_COOKIE_SECURE', True)
        SECURE_HSTS_SECONDS = get_int_env('SECURE_HSTS_SECONDS', 31536000)
        SECURE_HSTS_INCLUDE_SUBDOMAINS = get_bool_env('SECURE_HSTS_INCLUDE_SUBDOMAINS', True)
        SECURE_HSTS_PRELOAD = get_bool_env('SECURE_HSTS_PRELOAD', True)
        SECURE_CONTENT_TYPE_NOSNIFF = True
        X_FRAME_OPTIONS = 'DENY'
    ```
- **Rationale:** Addresses all 6 deployment warnings flagged by `python manage.py check --deploy`. When in production (`DEBUG=False`), strict SSL redirect, HSTS header, secure cookies, and clickjacking protections are automatically enforced.
- **Verification:** `python manage.py check --deploy` passes with `0 issues (0 silenced)`.

---

### 2.2 `static/js/api_client.js`
- **Category:** API Client Architecture & Live UI Consumer
- **Changes:**
  - Re-aligned method URL targets with canonical backend routes in `scholar_lens/api.py`:
    - `getOpenings(params)` -> `GET /api/openings/`
    - `getFundingCalls(params)` -> `GET /api/funding-calls/`
    - `getAnalyticsResearch(params)` -> `GET /api/analytics/research/`
    - Added `getBookings(params)` -> `GET /api/bookings/`
    - Added `getProjects(params)` -> `GET /api/projects/`
  - Added backward-compatibility aliases:
    - `getOpportunities(params)` -> calls `getOpenings(params)`
    - `getGrants(params)` -> calls `getFundingCalls(params)`
    - `getAnalytics(params)` -> calls `getAnalyticsResearch(params)`
  - Implemented live UI consumer: `initHeaderLiveSearch()`:
    - Attaches event listeners to `.ums-header-search input[name="q"]`.
    - Implements a 300ms debounce timer to prevent network flooding.
    - Enforces $\ge 2$ characters search threshold.
    - Issues parallel asynchronous requests to `/api/search/expertise/` and `/api/publications/`.
    - Renders interactive dropdown with loading spinner, empty state notification, result cards with match badges, and graceful error handling.
    - Handles Escape key dismissal and click-outside closing.
- **Verification:** Tested in browser, verified via `tests.test_p08_gaps.ApiTest`.

---

### 2.3 `templates/base.html`
- **Category:** UI Shell & Access Control
- **Changes:**
  - Fixed Django Administration navigation link condition on line 73:
    - *Before:* `{% if user.is_superuser %}`
    - *After:* `{% if user.is_staff or user.is_superuser %}`
  - Ensured header live search dropdown container is properly positioned below the search bar.
- **Rationale:** Enables institutional Research Office staff members who hold `is_staff` privileges to access the Django admin portal without requiring full superuser root permissions.
- **Verification:** `tests.test_ums_shell.UmsShellTest` passed 7/7; Cypress `01_shell.cy.js` passed 9/9.

---

### 2.4 `static/css/style.css`
- **Category:** Accessibility & WCAG 2.1 AA Compliance
- **Changes:**
  - Updated `.book-teal .book-cover` background from `#148F82` to high-contrast forest teal `#093b35`.
  - Updated `.book-teal .book-sub-mini` text color from `var(--color-yellow)` (`#f37021`) to light yellow `#fef08a`.
- **Rationale:** Axe-Core automated accessibility audit flagged an insufficient contrast ratio ($3.97:1$ vs $4.5:1$ threshold) on the landing page ambient card. The new palette raises the contrast ratio to $> 10:1$, exceeding WCAG AA and AAA requirements.
- **Verification:** Cypress `13_accessibility.cy.js` passed with 0 accessibility violations across all 11 core application views.

---

### 2.5 `cypress.config.js`
- **Category:** E2E Test Configuration
- **Changes:**
  - Exported configuration object directly (`module.exports = { ... }`) rather than relying on `const { defineConfig } = require('cypress')`.
- **Rationale:** Prevents Webpack bundling errors in environments where Cypress binary is globally cached rather than duplicated in local node_modules.
- **Verification:** All 13 Cypress test suites executed cleanly in headless Electron.

---

### 2.6 Database Migrations & Environment Synchronization
- **Category:** Relational Database Infrastructure
- **Actions:**
  - Applied all 47 database migrations across all 15 Django apps to the live PostgreSQL 16 database `scholar_lens`.
  - Created and migrated `scholar_lens_e2e` for deterministic Cypress browser testing.
  - Executed `collectstatic --noinput` to synchronize static assets into `staticfiles/`.
- **Verification:** `python manage.py showmigrations` confirms `[X]` across all apps; `check` confirms zero database issues.
