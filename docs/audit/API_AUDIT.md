# Scholar Lens — Comprehensive API Audit Report

**Document Version:** 1.0.0  
**Audit Date:** November 6, 2026  
**Auditor:** API Integration Engineer & Senior Django Architect  
**Scope:** P08 Public Read-Only JSON APIs, Internal Action Endpoints, and Async Services  

---

## 1. Executive Summary

Scholar Lens exposes two categories of endpoints:
1. **The 9 P08 Institutional JSON APIs (spec §8):** Located in `scholar_lens/api.py`, mapped under `/api/*`. Read-only, session-authenticated (`401 JSON` when unauthenticated), rate-capped by default, supporting `?limit=` (max 100).
2. **Internal Functional API & Action Endpoints:** Specialized AJAX/JSON endpoints powering graph visualizations, RAG paper chat, status decisions, and export services across individual Django apps.

All 9 P08 endpoints are fully implemented and verified with automated test coverage. This audit records their interface contracts, schemas, permissions, dependencies, and frontend consumption status.

---

## 2. P08 Institutional JSON APIs (`scholar_lens/api.py`)

### 2.1 Researcher Profiles API
- **Endpoint:** `GET /api/researchers/`
- **Authentication:** Session authenticated (`@api_login_required`)
- **Required Role:** Any authenticated user
- **Query Parameters:**
  - `department` (optional string): Filter by department code (e.g. `?department=CSE`)
  - `limit` (optional integer): Result limit, $1 \le \text{limit} \le 100$ (default: 50)
- **Response Structure (200 OK):**
  ```json
  {
    "results": [
      {
        "id": 14,
        "username": "dr_patel",
        "name": "Dr. Rajesh Patel",
        "department": "Computer Science & Engineering",
        "headline": "Associate Professor in Distributed Systems",
        "orcid_id": "0000-0002-1825-0097",
        "scopus_id": "57200000000",
        "verification_status": "VERIFIED",
        "available_for_collaboration": true,
        "interests": ["Distributed Consensus", "Cloud Infrastructure"],
        "skills": ["Go", "Kubernetes", "Formal Verification"]
      }
    ]
  }
  ```
- **Error Responses:** `401 Unauthorized` (`{"error": "authentication required"}`)
- **Frontend Consumer:** Researcher directory search suggestions, collaboration modal.
- **Database Dependencies:** `researchers.ResearcherProfile`, `researchers.Department`, `researchers.ResearchInterest`, `researchers.Skill`.
- **Test Coverage:** `tests/test_p08_gaps.py::test_api_researchers`
- **Implementation Status:** `WORKING`

---

### 2.2 Expertise Search API
- **Endpoint:** `GET /api/search/expertise/`
- **Authentication:** Session authenticated (`@api_login_required`)
- **Required Role:** Any authenticated user
- **Query Parameters:**
  - `q` (required string): Free-text expertise query (e.g. `?q=Quantum+Error+Correction`)
  - `department` (optional string): Filter by department code
  - `limit` (optional integer): Result limit, max 100
- **Response Structure (200 OK):**
  ```json
  {
    "query": "Quantum Error Correction",
    "results": [
      {
        "id": 7,
        "username": "prof_alvarez",
        "name": "Prof. Elena Alvarez",
        "department": "Physics & Nanotechnology",
        "headline": "Senior Quantum Scientist",
        "orcid_id": "0000-0001-9283-4412",
        "scopus_id": "57199999999",
        "verification_status": "VERIFIED",
        "available_for_collaboration": true,
        "interests": ["Quantum Computation", "Topological Codes"],
        "skills": ["Qiskit", "Superconducting Qubits"],
        "rank": 0.8924
      }
    ]
  }
  ```
- **Error Responses:** `400 Bad Request` (`{"error": "q is required"}`), `401 Unauthorized`
- **Database Dependencies:** PostgreSQL `SearchVectorField` on `ResearcherProfile`, `SearchQuery`, `SearchRank`.
- **Test Coverage:** `tests/test_expertise_search.py`, `tests/test_p08_gaps.py`
- **Implementation Status:** `WORKING`

---

### 2.3 Publication Register API
- **Endpoint:** `GET /api/publications/`
- **Authentication:** Session authenticated (`@api_login_required`)
- **Required Role:** Any authenticated user
- **Query Parameters:**
  - `year` (optional integer): Filter by publication year (e.g. `?year=2025`)
  - `limit` (optional integer): Result limit, max 100
- **Response Structure (200 OK):**
  ```json
  {
    "results": [
      {
        "id": 102,
        "title": "Decentralized Federated Learning on Non-IID Datasets",
        "year": 2025,
        "venue": "IEEE Transactions on Neural Networks",
        "doi": "10.1109/TNNLS.2025.100234",
        "pub_type": "JOURNAL",
        "source": "CROSSREF",
        "authors": ["Rajesh Patel", "Elena Alvarez", "Marcus Vance"]
      }
    ]
  }
  ```
- **Filter Constraint:** Only returns non-merged active papers (`merged_into__isnull=True`) via `ResearchPaper.objects`.
- **Error Responses:** `401 Unauthorized`
- **Database Dependencies:** `papers.ResearchPaper`, `papers.PaperAuthor`.
- **Test Coverage:** `tests/test_publications.py`, `tests/test_p08_gaps.py`
- **Implementation Status:** `WORKING`

---

### 2.4 Research Openings API
- **Endpoint:** `GET /api/openings/`
- **Authentication:** Session authenticated (`@api_login_required`)
- **Required Role:** Any authenticated user
- **Query Parameters:**
  - `limit` (optional integer): Max 100
- **Response Structure (200 OK):**
  ```json
  {
    "results": [
      {
        "id": 5,
        "title": "Graduate Researcher in Neuromorphic Architectures",
        "department": "Computer Science & Engineering",
        "project_id": 12,
        "required_skills": ["PyTorch", "Spiking Neural Networks"],
        "spots_available": 2,
        "deadline": "2026-12-15"
      }
    ]
  }
  ```
- **Filter Constraint:** Strictly returns openings with `status='OPEN'`.
- **Error Responses:** `401 Unauthorized`
- **Database Dependencies:** `opportunities.ResearchOpening`, `opportunities.Skill`.
- **Test Coverage:** `tests/test_opportunities.py`, `tests/test_p08_gaps.py`
- **Implementation Status:** `WORKING`

---

### 2.5 Research Projects API
- **Endpoint:** `GET /api/projects/`
- **Authentication:** Session authenticated (`@api_login_required`)
- **Required Role:** Any authenticated user (Row-level filtering enforced)
- **Scope & Security Rules:** Non-staff users receive public projects plus projects where they are leader or enlisted member. Staff receive all institutional projects.
- **Query Parameters:**
  - `limit` (optional integer): Max 100
- **Response Structure (200 OK):**
  ```json
  {
    "results": [
      {
        "id": 12,
        "title": "Fault-Tolerant Quantum Algorithms",
        "leader": "prof_alvarez",
        "status": "ACTIVE",
        "research_area": "QUANTUM",
        "start_date": "2025-01-01",
        "end_date": "2027-12-31",
        "milestones": [
          {
            "id": 31,
            "title": "Syndrome Extraction Circuit Benchmark",
            "due_date": "2026-11-30",
            "status": "IN_PROGRESS",
            "progress": 65,
            "risk": "ON_TRACK"
          }
        ]
      }
    ]
  }
  ```
- **Error Responses:** `401 Unauthorized`
- **Database Dependencies:** `projects.ResearchProject`, `projects.Milestone`, `projects.ProjectMember`.
- **Test Coverage:** `tests/test_milestones.py`, `tests/test_p08_gaps.py`
- **Implementation Status:** `WORKING`

---

### 2.6 Facilities Directory API
- **Endpoint:** `GET /api/facilities/`
- **Authentication:** Session authenticated (`@api_login_required`)
- **Required Role:** Any authenticated user
- **Query Parameters:**
  - `limit` (optional integer): Max 100
- **Response Structure (200 OK):**
  ```json
  {
    "results": [
      {
        "id": 3,
        "name": "NVIDIA H100 GPU Supercomputing Cluster",
        "kind": "COMPUTE",
        "department": "Computer Science & Engineering",
        "location": "Central Computing Wing, Room 402",
        "capacity": 8,
        "requires_approval": true,
        "opening_hours": [
          { "weekday": 0, "opens": "08:00:00", "closes": "22:00:00" },
          { "weekday": 1, "opens": "08:00:00", "closes": "22:00:00" }
        ]
      }
    ]
  }
  ```
- **Filter Constraint:** Only returns `is_active=True` facilities.
- **Error Responses:** `401 Unauthorized`
- **Database Dependencies:** `facilities.Facility`, `facilities.FacilitySlot`.
- **Test Coverage:** `tests/test_facilities.py`, `tests/test_p08_gaps.py`
- **Implementation Status:** `WORKING`

---

### 2.7 Facility Bookings API
- **Endpoint:** `GET /api/bookings/`
- **Authentication:** Session authenticated (`@api_login_required`)
- **Required Role:** Authenticated (Non-staff see own bookings + bookings on facilities they manage as custodian; staff see all).
- **Query Parameters:**
  - `limit` (optional integer): Max 100
- **Response Structure (200 OK):**
  ```json
  {
    "results": [
      {
        "id": 45,
        "facility": "NVIDIA H100 GPU Supercomputing Cluster",
        "user": "dr_patel",
        "start": "2026-11-10T09:00:00Z",
        "end": "2026-11-10T13:00:00Z",
        "status": "APPROVED",
        "purpose": "Distributed LLM fine-tuning validation"
      }
    ]
  }
  ```
- **Error Responses:** `401 Unauthorized`
- **Database Dependencies:** `facilities.Booking`, `facilities.Facility`.
- **Test Coverage:** `tests/test_facilities.py`, `tests/test_p08_gaps.py`
- **Implementation Status:** `WORKING`

---

### 2.8 Funding Calls API
- **Endpoint:** `GET /api/funding-calls/`
- **Authentication:** Session authenticated (`@api_login_required`)
- **Required Role:** Any authenticated user
- **Query Parameters:**
  - `open` (optional boolean string): If `'true'`, filters `deadline >= now()`
  - `limit` (optional integer): Max 100
- **Response Structure (200 OK):**
  ```json
  {
    "results": [
      {
        "id": 9,
        "title": "National Science Foundation: Frontier AI Infrastructure",
        "sponsor": "NSF",
        "research_area": "ARTIFICIAL_INTELLIGENCE",
        "amount": "500000.00",
        "deadline": "2026-12-01T17:00:00Z",
        "state": "OPEN",
        "url": "https://www.nsf.gov/funding/pgm_summ.jsp"
      }
    ]
  }
  ```
- **Filter Constraint:** Only returns `is_published=True` funding calls.
- **Error Responses:** `401 Unauthorized`
- **Database Dependencies:** `funding.FundingCall`.
- **Test Coverage:** `tests/test_funding.py`, `tests/test_p08_gaps.py`
- **Implementation Status:** `WORKING`

---

### 2.9 Institutional Research Analytics API
- **Endpoint:** `GET /api/analytics/research/`
- **Authentication:** Session authenticated (`@api_login_required`)
- **Required Role:** **Research Office staff or Dean of Research ONLY.**
- **Confidentiality Enforcement:**
  - Non-Dean/Non-Staff: `403 Forbidden` (`{"error": "Research Office or Dean of Research only"}`).
  - Research Office staff: Returns aggregated departmental productivity, publications count, funding metrics, and facility utilization.
  - Dean of Research (`is_dean(user)`): Includes **confidential individual per-researcher productivity metrics**.
- **Query Parameters:**
  - `year` (optional string): Academic year identifier (e.g. `?year=2025-26`). Defaults to current academic year (July 1 - June 30).
- **Response Structure (200 OK, Dean View):**
  ```json
  {
    "academic_year": "2025-26",
    "window_start": "2025-07-01T00:00:00Z",
    "window_end": "2026-06-30T23:59:59Z",
    "publications_count": 84,
    "proposals_submitted": 22,
    "proposals_awarded": 9,
    "funding_success_rate": 40.9,
    "total_funding_awarded": "2450000.00",
    "facility_booking_hours": 1420.5,
    "department_breakdown": [
      {
        "department": "Computer Science & Engineering",
        "papers": 42,
        "funding": "1200000.00",
        "hours": 850.0
      }
    ],
    "researcher_productivity": [
      {
        "researcher_id": 14,
        "name": "Dr. Rajesh Patel",
        "department": "Computer Science & Engineering",
        "papers_published": 8,
        "grants_awarded": 2,
        "facility_hours": 120.0
      }
    ]
  }
  ```
- **Error Responses:** `401 Unauthorized`, `403 Forbidden`
- **Database Dependencies:** Aggregations across `papers`, `funding`, `facilities`, and `researchers`.
- **Test Coverage:** `tests/test_analytics.py`, `tests/test_p08_gaps.py`
- **Implementation Status:** `WORKING`

---

## 3. Internal Asynchronous & Action Endpoints

| Endpoint | HTTP Method | Auth / Permission | Function / Purpose | Response Format |
|---|---|---|---|---|
| `/collaboration/graph/data/` | `GET` | Authenticated | Generates Cytoscape.js nodes & edges for institutional collaboration graph | JSON `{ "elements": { "nodes": [...], "edges": [...] } }` |
| `/ai/api/ask/<paper_id>/` | `POST` | Authenticated | Asynchronous question-answering for Ask Your Paper RAG assistant | JSON `{ "response": "...", "sources": [...] }` |
| `/facilities/bookings/<id>/decide/` | `POST` | Custodian / Staff | Approves or rejects facility booking slot request | Redirect / JSON confirmation |
| `/facilities/bookings/<id>/cancel/` | `POST` | Owner / Custodian | Cancels active or pending booking | Redirect with alert message |
| `/facilities/bookings/<id>/calendar.ics` | `GET` | Participant | Generates RFC 5545 iCalendar stream for calendar import | `text/calendar; charset=utf-8` attachment |
| `/funding/<id>/alert/` | `POST` | Authenticated | Subscribes/unsubscribes current user to funding deadline notifications | JSON `{ "status": "subscribed" \| "unsubscribed" }` |
| `/projects/milestones/<id>/progress/` | `POST` | Project Leader / Staff | Updates progress percentage and updates milestone risk status | JSON `{ "progress": 85, "risk": "ON_TRACK" }` |
| `/papers/authors/<id>/claim/` | `POST` | Authenticated | Researcher self-claims paper author entry | Redirect with pending verification notice |
| `/papers/authors/<id>/decide/` | `POST` | Staff / Office | Accepts or rejects author disambiguation candidate | Redirect with audit log confirmation |
| `/papers/dedup/<id>/decide/` | `POST` | Staff / Office | Executes automated or manual paper merge | Redirect with audit log confirmation |
| `/papers/<id>/unmerge/` | `POST` | Staff / Office | Idempotently restores a soft-merged duplicate paper | Redirect with audit log confirmation |
| `/analytics/research/export.csv` | `GET` | Staff / Dean | Downloads academic-year productivity report in CSV format | `text/csv` stream with `Content-Disposition` |

---

## 4. Audit Conclusions & Frontend Integration Strategy

1. **Endpoint Completeness:** All 9 required P08 JSON APIs exist, return correct schema fields, and strictly enforce the authorization matrix.
2. **Session Authentication:** The decorator `@api_login_required` returns standard `401 JSON` payloads, ensuring SPA and AJAX consumers can catch unauthenticated states cleanly.
3. **Frontend Integration Gap:** Currently, several frontend list views (such as research openings and facilities) render exclusively via Django SSR templates. In Phase 4, we will introduce a lightweight institutional client service (`static/js/api_client.js`) that wraps these endpoints for fast asynchronous filtering, live search hints, and seamless updates.
