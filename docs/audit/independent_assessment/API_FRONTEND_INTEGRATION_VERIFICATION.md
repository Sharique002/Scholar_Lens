# Scholar Lens — API and Frontend Integration Forensic Verification

**Document Version:** 1.0.0  
**Audit Date:** November 6, 2026  
**Auditor:** Independent Principal Software Auditor & API Architect  

---

## 1. Executive Summary

A forensic inspection was performed comparing the backend API implementation in `scholar_lens/api.py` against the client-side JavaScript module `static/js/api_client.js` and the application's template views.

### Key Audit Findings:
1. **The Backend JSON API Is Functional and Hardened:**  
   All 9 P08 endpoints defined in `scholar_lens/api.py` exist, enforce authentication (returning `401 {"error": "authentication required"}` for anonymous requests), return real database records, and pass automated tests in `tests/test_p08_gaps.py`.
2. **Identification of the Exact 9th Endpoint:**  
   The 9 backend P08 routes are:
   1. `GET /api/researchers/` (M1: Researcher directory)
   2. `GET /api/publications/` (M2: Publications register)
   3. `GET /api/search/expertise/` (M3: Full-text expertise search)
   4. `GET /api/openings/` (M4: Research openings & opportunities)
   5. `GET /api/projects/` (M8: Projects & milestone status)
   6. `GET /api/facilities/` (M6: Facilities directory & hours)
   7. `GET /api/bookings/` (M6: Facility reservations & custodian status)
   8. `GET /api/funding-calls/` (M7: Funding calls register)
   9. `GET /api/analytics/research/` (M9: Dean confidential metrics)
   
   The 9th endpoint is **`GET /api/bookings/`**, which manages facility booking schedules and custodian approvals.
3. **Route Mismatches in `static/js/api_client.js`:**  
   The client module created in Phase 4 contained naming divergences from `scholar_lens/api.py`:
   - It targeted `/api/opportunities/` instead of `/api/openings/`.
   - It targeted `/api/funding/` instead of `/api/funding-calls/`.
   - It targeted `/api/analytics/overview/` instead of `/api/analytics/research/`.
   - It attempted detail lookups (`/api/researchers/<id>/`, `/api/facilities/<id>/`) that do not exist on the backend (the backend provides list and filtered endpoints with `?limit=`).
   - It omitted methods for `/api/bookings/` and `/api/projects/`.
4. **Frontend Architecture Status:**  
   The Scholar Lens frontend is predominantly an **institutional server-rendered architecture** (Django templates rendering ORM QuerySets). While `api_client.js` is loaded globally via `base.html`, primary page navigation, table rendering, and form submissions operate via server-side Django views. The frontend API client is **PARTIAL** and not actively consumed by page templates.

---

## 2. Nine-Endpoint Verification Matrix

| Endpoint | Route Exists | Backend Works | Auth Enforced | Role Gating | Frontend Connected | CSRF Handled | Request Params | Response Structure | DB Records Returned | Automated Tests |
|---|---|---|---|---|---|---|---|---|---|---|
| **1. `/api/researchers/`** | **YES** | **YES** | **YES (401)** | All Authenticated | Partial (Helper only) | N/A (GET) | `?department=`, `?limit=` | `{"results": [...]}` | **YES** | `test_p08_gaps.py` |
| **2. `/api/publications/`** | **YES** | **YES** | **YES (401)** | All Authenticated | No (SSR) | N/A (GET) | `?year=`, `?limit=` | `{"results": [...]}` | **YES** | `test_p08_gaps.py` |
| **3. `/api/search/expertise/`** | **YES** | **YES** | **YES (401)** | All Authenticated | Partial (Live binder) | N/A (GET) | `?q=`, `?department=`, `?limit=` | `{"query": ..., "results": [...]}` | **YES** | `test_expertise_search.py`, `test_p08_gaps.py` |
| **4. `/api/openings/`** | **YES** | **YES** | **YES (401)** | All Authenticated | No (SSR) | N/A (GET) | `?limit=` | `{"results": [...]}` | **YES** | `test_p08_gaps.py` |
| **5. `/api/projects/`** | **YES** | **YES** | **YES (401)** | Member / Staff | No (SSR) | N/A (GET) | `?limit=` | `{"results": [...]}` | **YES** | `test_p08_gaps.py` |
| **6. `/api/facilities/`** | **YES** | **YES** | **YES (401)** | All Authenticated | No (SSR) | N/A (GET) | `?limit=` | `{"results": [...]}` | **YES** | `test_p08_gaps.py` |
| **7. `/api/bookings/`** | **YES** | **YES** | **YES (401)** | User / Custodian / Staff | No (SSR) | N/A (GET) | `?limit=` | `{"results": [...]}` | **YES** | `test_p08_gaps.py` |
| **8. `/api/funding-calls/`** | **YES** | **YES** | **YES (401)** | All Authenticated | No (SSR) | N/A (GET) | `?open=true`, `?limit=` | `{"results": [...]}` | **YES** | `test_p08_gaps.py` |
| **9. `/api/analytics/research/`** | **YES** | **YES** | **YES (401)** | **Staff / Dean (403)** | No (SSR) | N/A (GET) | `?year=` | `{"academic_year": ..., "dept_metrics": ...}` | **YES** | `test_analytics.py`, `test_p08_gaps.py` |

---

## 3. Discrepancy Reconciliation in `static/js/api_client.js`

The table below documents the discrepancies identified in `static/js/api_client.js`:

| Method in `api_client.js` | Endpoint Called by JS | Actual Backend Endpoint in `scholar_lens/api.py` | Evaluation |
|---|---|---|---|
| `getResearchers(params)` | `/api/researchers/` | `/api/researchers/` | **MATCH** |
| `getResearcher(id)` | `/api/researchers/<id>/` | *(None - handled via HTML route `/researchers/<id>/`)* | **ROUTE MISSING IN API** |
| `getPublications(params)` | `/api/publications/` | `/api/publications/` | **MATCH** |
| `getPublication(id)` | `/api/publications/<id>/` | *(None - handled via HTML route `/papers/<id>/`)* | **ROUTE MISSING IN API** |
| `searchExpertise(params)` | `/api/search/expertise/` | `/api/search/expertise/` | **MATCH** |
| `getOpportunities(params)` | `/api/opportunities/` | `/api/openings/` | **MISMATCH (404)** |
| `getCollaborations(params)` | `/api/collaboration/` | *(None - handled via `/collaboration/` view)* | **ROUTE MISSING IN API** |
| `getFacilities(params)` | `/api/facilities/` | `/api/facilities/` | **MATCH** |
| `getFacility(id)` | `/api/facilities/<id>/` | *(None - handled via HTML route `/facilities/<id>/`)* | **ROUTE MISSING IN API** |
| `getFundingCalls(params)` | `/api/funding/` | `/api/funding-calls/` | **MISMATCH (404)** |
| `getAnalyticsOverview()` | `/api/analytics/overview/` | `/api/analytics/research/` | **MISMATCH (404)** |
| *(None)* | *(Not implemented)* | `/api/bookings/` | **OMITTED FROM JS CLIENT** |
| *(None)* | *(Not implemented)* | `/api/projects/` | **OMITTED FROM JS CLIENT** |

---

## 4. Integration Verdict

- **Backend P08 API:** **FULLY VERIFIED (100% Passing)**.
- **Frontend Asynchronous API Integration:** **PARTIALLY IMPLEMENTED**. The client script exists and provides scaffolding, but contains endpoint URL mismatches and is not actively wired into the server-rendered template views.
