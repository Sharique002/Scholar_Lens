# End-to-End Testing Guide (Cypress)

This document describes how to configure, start, and run the Cypress end-to-end (E2E) testing suite for Scholar Lens.

---

## 1. Prerequisites

1. **Python 3.11** virtual environment with dependencies installed:
   ```bash
   .venv\Scripts\pip install -r requirements.txt
   ```
2. **PostgreSQL 15** running on Docker:
   ```bash
   docker compose up -d db
   ```
3. **Node.js 18+ and npm**:
   Dependencies pinned in `package.json`:
   - `cypress@13.15.0`
   - `cypress-axe@1.5.0`
   - `axe-core@4.10.0`
   Install with:
   ```bash
   npm install
   ```
4. **Dedicated E2E Database**:
   The E2E test suite executes against an isolated PostgreSQL database `scholar_lens_e2e`.
   ```bash
   docker exec -i scholar_lens_research_hub-db-1 psql -U scholar_lens -d postgres -c "CREATE DATABASE scholar_lens_e2e OWNER scholar_lens;"
   ```

---

## 2. Configuration (`cypress.env.json`)

Copy `cypress.env.example.json` to `cypress.env.json` (this file is gitignored and must never be committed):

```json
{
  "PYTHON": ".venv\\Scripts\\python.exe",
  "E2E_DATABASE_URL": "postgres://scholar_lens:scholar_lens@localhost:5432/scholar_lens_e2e",
  "E2E_PASSWORD": "TestPassword123!"
}
```

---

## 3. Starting the E2E Test Server

Run the test server on port `8001` with `E2E=1` and pointing to the `scholar_lens_e2e` database:

### Windows PowerShell:
```powershell
$env:E2E="1"
$env:DATABASE_URL="postgres://scholar_lens:scholar_lens@localhost:5432/scholar_lens_e2e"
$env:USE_POSTGRES="1"
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py e2e_reset
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001
```

### Linux / macOS:
```bash
E2E=1 DATABASE_URL=postgres://scholar_lens:scholar_lens@localhost:5432/scholar_lens_e2e .venv/bin/python manage.py migrate
E2E=1 DATABASE_URL=postgres://scholar_lens:scholar_lens@localhost:5432/scholar_lens_e2e .venv/bin/python manage.py e2e_reset
E2E=1 DATABASE_URL=postgres://scholar_lens:scholar_lens@localhost:5432/scholar_lens_e2e .venv/bin/python manage.py runserver 127.0.0.1:8001
```

---

## 4. Running the Tests

### Headless (Complete Suite):
```bash
npm run e2e
```
Or with npx:
```bash
npx cypress run --browser chrome
```

### Mobile Viewport (375px × 812px):
```bash
npm run e2e:mobile
```

### Interactive Test Runner (Headed):
```bash
npm run e2e:open
```

---

## 5. Test Suite Architecture

| Spec | Target | Scope |
|---|---|---|
| `01_shell.cy.js` | UI Shell & Nav | Desktop collapse, guest navigation, flat sidebar order, active nav, breadcrumbs, marquee strip, footer |
| `02_mobile.cy.js` | Mobile Responsive | 375px drawer, hamburger toggle, no horizontal scroll across key views |
| `03_dashboard.cy.js` | Quick Actions | 5 quick action cards, routing, research ticker |
| `04_facilities.cy.js` | M8 Facilities | Slot booking, double-booking exclusion constraint, back-to-back booking, closed hours check, custodian approval, cancellation, utilisation report & CSV |
| `05_funding.cy.js` | M6 Funding | Countdown pills, filter by area, watch toggle, scheduled alerts idempotency, 403 permission guard |
| `06_milestones.cy.js` | M7 Milestones | Timeline bars, cycle detection loop prevention, automated risk detection, at-risk board, 403 permission guard |
| `07_profiles.cy.js` | M1 Profiles | Department assignment, ISO 7064 MOD 11-2 ORCID checksum validation, verification request queue & approval |
| `08_publications.cy.js` | M2 Publications | Offline ORCID import, duplicate review & soft merge redirect, undo unmerge, author claim ("Is this you?" / "This is me") |
| `09_expertise_search.cy.js` | M3 Search | Faceted full-text search across departments, empty query hint, department facet filter, verified-only toggle |
| `10_collaboration.cy.js` | M5 Collaboration | Algorithmic suggestions ("Suggested for you"), dismiss action, Cytoscape graph canvas, fallback accessible table |
| `11_openings.cy.js` | M4 Openings | Recommended openings with match %, PDF validation, duplicate prevention, shortlist & accept workflow, application withdrawal |
| `12_reports.cy.js` | M9 Analytics | Academic-year reporting, year selector, Dean-only confidential productivity table, section=all CSV export |
| `13_accessibility.cy.js` | Accessibility | Axe core automated accessibility audit across all major portal views |

---

## 6. How to Add a New Spec

1. Create a new test file in `cypress/e2e/<number>_<name>.cy.js`.
2. Follow Cypress quality guidelines:
   - Call `cy.resetDb()` in `before()`.
   - Never use arbitrary `cy.wait(<ms>)` timeouts; wait on DOM state or intercept aliases.
   - Use accessible selectors (labels, button text, roles) rather than styling classes.
   - Assert user-visible outcomes.
