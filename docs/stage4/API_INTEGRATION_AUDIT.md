# Scholar Lens — Stage 4 API Integration Audit
**Document ID:** `DOC-S4-API-01`  
**Execution Date:** 2026-11-07  
**Auditor:** Independent Software Auditor & Principal API Integration Engineer  
**Status:** VERIFIED & SYNCHRONIZED  

---

## 1. Executive Summary

During Phase 4 of the Stage 4 Independent Final Verification and Production Acceptance Audit, all 9 canonical P08 REST API routes were evaluated for specification compliance, URL routing consistency, role-based authorization, rate/limit bounding, response structure, and frontend consumption.

The audit verified that:
1. All 9 endpoints in `scholar_lens/api.py` are active and registered under `/api/` in `scholar_lens/urls.py`.
2. The browser JavaScript client `static/js/api_client.js` maps 1:1 to every backend route with CSRF injection, exponential backoff, and 401 handling.
3. Every endpoint enforces authenticated access (`@api_login_required`), returning HTTP 401 for unauthorized callers.
4. Confidential endpoints (`/api/analytics/research/`) enforce strict Role-Based Access Control (RBAC), returning HTTP 403 for non-Dean / non-Research Office callers and redacting researcher productivity from non-Dean callers.
5. All endpoints enforce query result pagination caps (`limit` bounded to $\le 100$).
6. Live frontend consumer `initHeaderLiveSearch()` in `static/js/api_client.js` actively queries `/api/search/expertise/` and `/api/publications/` with debounce and loading states.

---

## 2. Canonical Route Synchronization Matrix

| # | P08 Module | Canonical Backend Route | View Function | JS Client Method | Auth Level | Verified Response Format |
|---|---|---|---|---|---|---|
| 1 | **M1: Profiles** | `GET /api/researchers/` | `api.researchers` | `getResearchers(params)` | Authenticated | `{"results": [{"id", "username", "name", "department", "headline", "interests", "skills", ...}]}` |
| 2 | **M2: Publications** | `GET /api/publications/` | `api.publications` | `getPublications(params)` | Authenticated | `{"results": [{"id", "title", "year", "venue", "doi", "pub_type", "source", "authors": []}]}` |
| 3 | **M3: Expertise** | `GET /api/search/expertise/?q=` | `api.expertise_search` | `searchExpertise(params)` | Authenticated | `{"query": "...", "results": [{"id", "name", "headline", "rank": 0.xxxx, ...}]}` |
| 4 | **M4: Openings** | `GET /api/openings/` | `api.openings` | `getOpenings(params)` | Authenticated | `{"results": [{"id", "title", "department", "project_id", "required_skills", "spots_available", "deadline"}]}` |
| 5 | **M5: Projects** | `GET /api/projects/` | `api.projects` | `getProjects(params)` | Authenticated (scoped) | `{"results": [{"id", "title", "leader", "status", "milestones": [{"id", "title", "due_date", "risk"}]}]}` |
| 6 | **M6: Facilities** | `GET /api/facilities/` | `api.facilities` | `getFacilities(params)` | Authenticated | `{"results": [{"id", "name", "kind", "location", "capacity", "opening_hours": []}]}` |
| 7 | **M6: Bookings** | `GET /api/bookings/` | `api.bookings` | `getBookings(params)` | Authenticated (scoped) | `{"results": [{"id", "facility", "user", "start", "end", "status", "purpose"}]}` |
| 8 | **M7: Funding** | `GET /api/funding-calls/` | `api.funding_calls` | `getFundingCalls(params)` | Authenticated | `{"results": [{"id", "title", "sponsor", "amount", "deadline", "state", "url"}]}` |
| 9 | **M9: Analytics** | `GET /api/analytics/research/` | `api.research_analytics` | `getAnalyticsResearch(params)` | Staff or Dean | `{"academic_year": "...", "total_papers", "department_breakdown", "researchers" (Dean only)}` |

---

## 3. Security, Authorization & Boundary Audits

### 3.1 Authentication & Status Codes
- Unauthenticated requests to all 9 endpoints return `{"error": "authentication required"}` with `status=401`.
- Verified via `tests.test_p08_gaps.ApiTest.test_api_endpoints_login_required`.

### 3.2 Granular RBAC & Confidentiality Protection
- Requesting `/api/analytics/research/` as an ordinary student or faculty user returns HTTP 403 `{"error": "Research Office or Dean of Research only"}`.
- Research Office staff can access institutional metrics, but individual researcher productivity rankings are excluded (`include_researchers=False`).
- Only Dean of Research receives the complete researcher productivity ranking array (`include_researchers=True`).
- Verified via `tests.test_institutional_search.InstitutionalSearchTest` and `tests.test_p08_gaps.ApiTest`.

### 3.3 Bounded Query Limits
- Every endpoint utilizes `_limit(request)` which clamps `limit = max(1, min(int(request.GET.get('limit', 50)), 100))`.
- Prevents database denial-of-service through arbitrary query result limits.

---

## 4. Frontend Consumer Verification

- `static/js/api_client.js` is included globally in `templates/base.html` line 172.
- `initHeaderLiveSearch()` attaches to `.ums-header-search input[name="q"]` with 300ms debounce, minimum 2-character query length, loading spinner, match badge highlighting, and keyboard navigation.
- Verified in browser and through Cypress test `01_shell.cy.js` ("header search for 'learning' redirects to search results").

---

## 5. Phase 4 Verification Conclusion

**Phase 4 API Integration Audit Verdict: PASSED — ALL 9 CANONICAL ENDPOINTS SYNCHRONIZED, SECURED, AND OPERATIONAL.**
