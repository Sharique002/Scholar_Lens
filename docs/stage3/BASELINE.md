# Scholar Lens — Stage 3 Baseline & Implementation Control

**Document Version:** 1.0.0  
**Baseline Timestamp:** 2026-11-06T17:50:00+05:30  
**Current Git Branch:** `p08_system_stabilization`  
**Current Commit:** `1e6e08d8d438c769697160a46551f358d3dadcc8`  
**Database Cluster:** PostgreSQL 16.15 on `127.0.0.1:5433` (WSL2 Ubuntu 24.04)  
**Django System Check:** System check identified no issues (0 silenced).  

---

## 1. Existing System State & Verified Baselines

### 1.1 Existing Functionality Verified:
- **Core Architecture:** 13 Django applications, 22 database models, 29 migrations.
- **AI Research Engine:** PDF text extraction, document chunking, OpenAI embeddings, paper summarization, research gap detection, grounded RAG Q&A, and 7-dimension evaluation engine (`ai_engine/` and `evaluation/`).
- **All 9 P08 Modules:** 
  - M1: Profiles, ORCID validation (ISO 7064 MOD 11-2), verification state machine.
  - M2: Publications, 3-stage deduplication (99.29% accuracy on 140 pairs), author disambiguation.
  - M3: Expertise search with PostgreSQL `pg_trgm` GIN indexing (71.76ms latency over 2,001 active profiles).
  - M4: Opportunities / openings board with PDF document upload.
  - M5: Collaboration matching engine with co-authorship gap bonus and Cytoscape graph.
  - M6: Facilities booking with PostgreSQL `btree_gist` ExclusionConstraint preventing concurrent overlaps.
  - M7: Funding register, automated deadline alert notifications (14/7/1 days), and RFC 5545 `.ics` generation.
  - M8: Project milestones, DFS cycle prevention, and nightly risk assessment.
  - M9: Academic year analytics (July 1 - June 30) with 100% Dean confidential privacy redaction.
- **Automated Tests:** 252 tests discovered across 19 test files in `tests/`, all 252 passing on PostgreSQL 16.

---

## 2. Unresolved Issues & Technical Debt from Stage 2 Forensic Audit

| Issue ID | Category | Component | Description | Remediation Plan |
|---|---|---|---|---|
| **ISSUE-01** | API | `static/js/api_client.js` | Endpoint URL mismatches: `/api/opportunities/` (should be `/api/openings/`), `/api/funding/` (should be `/api/funding-calls/`), `/api/analytics/overview/` (should be `/api/analytics/research/`). | Refactor `api_client.js` with canonical endpoint registry matching `scholar_lens/api.py`. |
| **ISSUE-02** | API | `static/js/api_client.js` | Omission of `/api/bookings/` and `/api/projects/`; non-existent detail endpoints called. | Add `getBookings` and `getProjects`; align methods with collection/filtered contracts. |
| **ISSUE-03** | Frontend Integration | Django Templates & JS | `api_client.js` is loaded globally in `base.html` but has no real active frontend consumers in the UI. | Implement interactive client-side consumers: live debounced expertise search modal/dropdown and quick-filter publication viewer. |
| **ISSUE-04** | Database | Main DB `scholar_lens` | All 29 migrations are unapplied on the main database (tests run on transient `test_scholar_lens`). | Execute `python manage.py migrate` on `scholar_lens` to provision all tables. |
| **ISSUE-05** | Testing | Cypress E2E | 13 Cypress specs in `cypress/e2e/` were not executed due to lack of a running server on port 8001. | Launch test server on port 8001 and execute Cypress test runner. |
| **ISSUE-06** | Auth / Cloud | Google OAuth | Live Google SSO is verified with mocks, but live production credentials and domain registration are pending. | Document exact Google Cloud Console setup and production domain authorization protocol. |
| **ISSUE-07** | Stylesheet | `static/css/style.css` | Residual legacy classes and unused keyframes in monolithic CSS file. | Clean up dead CSS and ensure full alignment with `institutional_tokens.css`. |

---

## 3. Stage 3 Task Register

| Task ID | Phase | Description | Assigned Responsibility | Acceptance Gate |
|---|---|---|---|---|
| **TASK-S3-01** | Phase 0 | Baseline & Implementation Control Documentation | Architect & Lead QA | `docs/stage3/BASELINE.md` created |
| **TASK-S3-02** | Phase 1 | Canonical API Endpoint Registry & Client Refactor | API Integration Engineer | `api_client.js` corrected, all 9 endpoints mapped |
| **TASK-S3-03** | Phase 1 | Frontend Real-Time Consumer Implementation | Frontend Engineer | Live debounced search & async filter consumers operational with loading/empty/error states |
| **TASK-S3-04** | Phase 1 | API Endpoint Automated Functional Tests | QA Engineer | Test coverage for all 9 API routes & frontend consumers (`docs/stage3/API_INTEGRATION_COMPLETION.md`) |
| **TASK-S3-05** | Phase 2 | Google OAuth Completion & Security Gating | Security Engineer | `docs/stage3/GOOGLE_OAUTH_COMPLETION.md` separating mocked, integration, live, and cloud tiers |
| **TASK-S3-06** | Phase 3 | Institutional UI/UX Remediation & Viewport Audits | Frontend & UI Lead | Verify viewports (1440, 1280, 1024, 768, 390, 360px), deliver `docs/stage3/UI_UX_COMPLETION.md` |
| **TASK-S3-07** | Phase 4 | P08 Modules (M1–M9) Focused Remediation & Proof | Principal Architect | Complete 9-module verification report (`docs/stage3/P08_MODULE_COMPLETION.md`) |
| **TASK-S3-08** | Phase 5 | Database Migration & Security Hardening | Database & Security Lead | Main DB migrated, security check pass, deliver `docs/stage3/DATABASE_SECURITY_COMPLETION.md` |
| **TASK-S3-09** | Phase 6 | P08 Deterministic Benchmark Reproduction | Performance Engineer | M2 (Dedup $\ge 95\%$), M3 (Search $<1\text{s}$), M6 (Concurrency), M9 (Privacy) documented |
| **TASK-S3-10** | Phase 7–9 | Complete Test Suite, Cypress E2E & Final Reports | QA Architect & Lead | Full test suite executed, Cypress E2E executed/documented, 14 reports in `docs/stage3/` |
