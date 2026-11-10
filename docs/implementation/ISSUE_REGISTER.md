# Scholar Lens — Technical Issue Register

**Document Version:** 1.0.0  
**Last Updated:** November 6, 2026  

---

## Active & Resolved Issue Log

| Issue ID | Severity | Category | Description | Root Cause | Proposed / Applied Solution | Status | Verification Target |
|---|---|---|---|---|---|---|---|
| **ISSUE-01** | High | UI / Design | Conflicting design systems between legacy neo-brutalist CSS (`style.css`, 57KB) and institutional UMS CSS (`ums.css`, 14KB). | `style.css` contains hardcoded 3.5px black borders, pastel boxes, and hard offset drop shadows loaded alongside UMS styles. | Consolidate tokens into `institutional_tokens.css`; refactor `style.css` to remove brutalist rules; unify palette to Maroon (`#9B2335`) and Orange (`#F37021`). | Open | Phase 2 |
| **ISSUE-02** | High | Auth / Nav | Fragile role check in `templates/base.html:108` (`'dean' in user.username.lower`). | `is_dean` and `is_office` helper functions existed in `dashboard.permissions` but were not injected into template context processors. | Update `scholar_lens/context_processors.py` to inject `is_dean` and `is_office` globally for all templates. | In Progress | Phase 1 |
| **ISSUE-03** | Medium | Database | Test suite execution failed on SQLite with `OperationalError: near "EXCLUDE": syntax error`. | `facilities.models.Booking` uses PostgreSQL-specific `ExclusionConstraint` and `RangeOperators.OVERLAPS` not supported on SQLite. | Configured active PostgreSQL 16 on port 5433 via WSL Ubuntu; test runner successfully executes against PostgreSQL. | Resolved | Phase 0 |
| **ISSUE-04** | Medium | UI / Responsive | Header search bar width fixed at 320px causes crowding on tablet and mobile viewports. | Fixed pixel width in `.ums-header-search`. | Change width to responsive fluid clamp (`clamp(180px, 25vw, 320px)`) and hide gracefully below 600px. | Open | Phase 2 |
| **ISSUE-05** | Medium | Auth / Security | Dynamic redirect URI in Google OAuth could mismatch reverse proxy hostnames in containerized deployments. | `get_redirect_uri` in `accounts/google_auth.py` needs strict HTTPS and trusted domain resolution. | Harden URI resolution and ensure `SECURE_PROXY_SSL_HEADER` is respected. | Open | Phase 3 |
| **ISSUE-06** | Low | UI / Accessibility | Milestone timeline SVG bars in Project detail lack descriptive `aria-label`. | SVG `<rect>` elements rendered without accessible descriptions. | Add `aria-label` detailing milestone title, due date, progress, and risk status. | Open | Phase 2 / Phase 6 |
| **ISSUE-07** | Medium | Frontend / API | Documented P08 JSON APIs are not systematically consumed by the frontend client. | Frontend list views rely strictly on full-page SSR without client-side API helper. | Create `static/js/api_client.js` with structured helper methods for live search, async filtering, and status updates. | Open | Phase 4 |
