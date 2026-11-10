# Scholar Lens — Cypress E2E Test Suite Forensic Audit

**Document Version:** 1.0.0  
**Audit Date:** November 6, 2026  
**Auditor:** Independent Principal Software Auditor & QA Automation Architect  
**Cypress Version:** 16.2.1 (Electron 41.7.0, Node 24.15.0)  

---

## 1. Executive Summary

A forensic audit of the end-to-end (E2E) testing suite was conducted by inspecting:
- `cypress.config.js` (E2E configuration file)
- `cypress/e2e/` (13 specification files)
- `package.json` (Node dependencies)

### Formal Status:
The entire Cypress E2E test suite is classified as **NOT EXECUTED**.  
Under the rules of this audit, Django unit and integration tests cannot and must not be substituted for browser-based E2E verification.

---

## 2. Specification Inventory & Scope of Coverage

The repository contains **13 Cypress E2E specifications** located in `cypress/e2e/`:

| Spec File | Target Scope | Key Verification Assertions | Execution Status |
|---|---|---|---|
| `01_shell.cy.js` | Institutional Portal Shell | Header rendering, maroon branding, sidebar navigation links, footer links | **NOT EXECUTED** |
| `02_mobile.cy.js` | Responsive Layout | Off-canvas mobile sidebar, hamburger menu toggle, mobile viewport reflow | **NOT EXECUTED** |
| `03_dashboard.cy.js` | Researcher Dashboard | 5 quick actions, 4 metrics strip cards, recent papers list, activity feed | **NOT EXECUTED** |
| `04_facilities.cy.js` | Facility Booking (M6) | Facility directory, modal booking form, conflicting booking rejection | **NOT EXECUTED** |
| `05_funding.cy.js` | Funding Register (M7) | Funding calls list, deadline countdowns, proposal application form | **NOT EXECUTED** |
| `06_milestones.cy.js` | Project Milestones (M8) | Milestone timeline, circular dependency prevention, at-risk flags | **NOT EXECUTED** |
| `07_profiles.cy.js` | Researcher Profiles (M1) | Taxonomy selector, ORCID checksum validation, verification state | **NOT EXECUTED** |
| `08_publications.cy.js` | Publications & Dedup (M2) | Publication upload, deduplication review queue, merge/unmerge actions | **NOT EXECUTED** |
| `09_expertise_search.cy.js` | Expertise Search (M3) | Real-time search query input, department facet filter, ranked cards | **NOT EXECUTED** |
| `10_collaboration.cy.js` | Collaboration Engine (M5) | Partner recommendations, invitation sending, Cytoscape graph canvas | **NOT EXECUTED** |
| `11_openings.cy.js` | Opportunities Board (M4) | Research openings, PDF document upload, candidate review | **NOT EXECUTED** |
| `12_reports.cy.js` | Research Analytics (M9) | Academic year picker, Dean privacy redactions, CSV download | **NOT EXECUTED** |
| `13_accessibility.cy.js` | Accessibility (a11y) | Automated axe-core WCAG 2.1 AA accessibility audit across core views | **NOT EXECUTED** |

---

## 3. Root Cause Analysis of Non-Execution

1. **Dedicated Server Dependency:**  
   In `cypress.config.js`, line 12 specifies:
   ```javascript
   baseUrl: 'http://127.0.0.1:8001',
   ```
   Cypress operates by connecting to a live running HTTP web server. The automated Django test runs (`manage.py test`) execute in-memory against a transient database and do not launch a persistent HTTP listener on port 8001.
2. **Database Seeding Prerequisite:**  
   The specifications require pre-populated seed data (specific demo users: `student`, `faculty`, `dean`, `admin`) that are not present in an unmigrated live database without running an explicit seed fixture command.
3. **Execution Environment Constraint:**  
   The automated background test runners operated in headless non-interactive mode.

---

## 4. Remediation Steps to Run E2E Tests

To execute the Cypress test suite in a local development environment:
1. Ensure the PostgreSQL database is migrated:
   ```powershell
   $env:DATABASE_URL="postgres://scholar_lens:scholar_lens@127.0.0.1:5433/scholar_lens"
   python manage.py migrate
   ```
2. Start the Django development server on port 8001:
   ```powershell
   python manage.py runserver 127.0.0.1:8001
   ```
3. In a separate terminal, trigger Cypress headless execution:
   ```bash
   npx cypress run --browser electron
   ```

---

## 5. Audit Conclusion

The Cypress E2E suite represents a valuable and complete set of 13 integration specifications, but it was **NOT EXECUTED** during this stabilization phase. Browser-level interaction, DOM animations, and live axe-core accessibility compliance remain formally **UNVERIFIED AT THE BROWSER TIER**.
