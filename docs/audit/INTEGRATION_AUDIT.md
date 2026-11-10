# Scholar Lens — Comprehensive External Integration Audit

**Document Version:** 1.0.0  
**Audit Date:** November 6, 2026  
**Auditor:** API Integration Engineer & Security Architect  
**Scope:** Identity Providers, Academic Indexes, AI Engines, Calendar Systems, and Visual Libraries  

---

## 1. Executive Summary

Scholar Lens integrates with external academic repositories, artificial intelligence providers, identity systems, and client libraries. This audit assesses the operational maturity, credential requirements, failure resilience, and fallback behaviors for each external service.

### Status Classifications:
- `FULLY_FUNCTIONAL`: Production-ready, operational with valid credentials, covered by automated tests.
- `IMPLEMENTED_PENDING_CREDENTIALS`: Implementation complete, tested with mocks/fixtures; awaits live production API keys.
- `PARTIALLY_IMPLEMENTED`: Core functionality implemented, but secondary capabilities (e.g. pagination or incremental harvesting) remain manual.
- `MOCKED`: Emulated via mock adapters for CI/CD and offline development.
- `BROKEN`: Failing requests, unhandled errors, or missing dependencies.

---

## 2. External Integration Assessment Matrix

### 2.1 Google OAuth 2.0 / OpenID Connect (SSO)
- **Primary Code Modules:** `accounts/google_auth.py`, `accounts/views.py`, `accounts/urls.py`
- **Configuration Variables:** `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_OAUTH_REDIRECT_URI`
- **Status:** `IMPLEMENTED_PENDING_CREDENTIALS` (with fully operational mock mode in `DEBUG`)
- **Protocol & Flow:** OpenID Connect Authorization Code Flow with PKCE state token validation.
- **Cryptographic Verification:**
  - Validates token claims (`iss` in `accounts.google.com`, `aud == GOOGLE_CLIENT_ID`, `exp > now()`, `email_verified == True`).
  - Uses `google-auth` (`google.oauth2.id_token.verify_oauth2_token`) with graceful fallback to `https://oauth2.googleapis.com/tokeninfo`.
- **Account Linking & Provisioning:**
  - Provisions or links user accounts via immutable Google `sub` (Subject ID) stored in `UserProfile.google_sub`.
  - Links existing accounts matching verified primary email.
- **Resilience & Fallback:**
  - In `DEBUG=True` or `mock=1`, provides `/accounts/google/mock/` simulating authentic Google identity tokens for seamless testing.
  - In production (`DEBUG=False`), displays clean institutional error messaging if `.env` keys are unconfigured.
- **Verification Evidence:** `tests/test_google_auth.py` (8 passing test cases).

---

### 2.2 OpenAI Intelligence Engine (Summarization, Gaps, RAG, Evaluation)
- **Primary Code Modules:** `ai_engine/services.py`, `evaluation/services.py`, `scholar_lens/settings.py`
- **Configuration Variables:** `OPENAI_API_KEY`, `OPENAI_MODEL` (default: `gpt-4o-mini`), `OPENAI_EMBEDDING_MODEL` (default: `text-embedding-3-small`)
- **Status:** `IMPLEMENTED_PENDING_CREDENTIALS` (with deterministic fallback heuristics)
- **Capabilities Implemented:**
  1. *Paper Summarization:* Extracts core hypotheses, methodology, and conclusions.
  2. *Research Gap Detection:* Identifies actionable future research trajectories.
  3. *Ask Your Paper (RAG):* Chunks PDF text into semantic units (`PaperChunk`), matches queries via embeddings or cosine similarity, and synthesizes grounded answers with page citations.
  4. *7-Dimension Novelty Evaluation:* Evaluates papers against canonical weights summing to 100% (Novelty 20%, Research Gap 15%, Methodology 15%, Contribution 15%, Evidence Quality 15%, Technical Strength 10%, Clarity 10%).
- **Resilience & Fallback:**
  - If `OPENAI_API_KEY` is not present, services catch configuration errors gracefully and provide local heuristic evaluations or informative UI badges (`AI Service Not Configured`). No fatal crashes occur.
- **Verification Evidence:** `tests/test_scholar_lens.py::AIServiceTestCase`, `tests/test_scholar_lens.py::EvaluationEngineTestCase`.

---

### 2.3 ORCID Public API (v3.0)
- **Primary Code Modules:** `papers/importers.py`, `papers/management/commands/import_publications.py`, `researchers/models.py`
- **Endpoint:** `https://pub.orcid.org/v3.0/{orcid_id}/works`
- **Authentication:** Public read-only API (no commercial licence key required).
- **Status:** `FULLY_FUNCTIONAL`
- **Capabilities Implemented:**
  - Strictly validates ORCID format via **ISO 7064 MOD 11-2 checksum algorithm** in `researchers.models.validate_orcid_id`.
  - Ingests work summaries, normalizes titles, parses publication dates and DOIs.
  - Automatically deduplicates fetched records against existing catalog using `papers.dedup.find_duplicate`.
  - Tracks ingestion runs in `papers.ImportRun` with counts of imported, duplicated, and skipped records.
- **Resilience & Fallback:**
  - Skips malformed work summaries (missing titles, invalid years, nested HTML) without aborting the batch.
  - Supports offline E2E test fixtures (`tests/fixtures/orcid_sample.json`).
- **Verification Evidence:** `tests/test_import.py::test_import_resilient_to_malformed`, `tests/test_profiles.py`.

---

### 2.4 Crossref REST API
- **Primary Code Modules:** `papers/importers.py`, `papers/management/commands/import_publications.py`
- **Endpoint:** `https://api.crossref.org/works`
- **Authentication:** Public REST API with Polite Pool User-Agent (`ScholarLens/1.0 (mailto:scholar.lens@university.edu)`).
- **Status:** `FULLY_FUNCTIONAL`
- **Capabilities Implemented:**
  - Keyword and title queries with configurable row limits.
  - DOI extraction, container-title (venue) mapping, and author list parsing.
  - Automatically avoids duplicates via exact DOI match and fuzzy title normalization.
- **Resilience & Fallback:**
  - Rate-limiting handled via Polite Pool headers.
  - Offline test fixture available (`tests/fixtures/crossref_sample.json`).
- **Verification Evidence:** `tests/test_import.py::test_crossref_import_flow`.

---

### 2.5 Elsevier Scopus Search API
- **Primary Code Modules:** `papers/importers.py`, `papers/management/commands/import_publications.py`
- **Endpoint:** `https://api.elsevier.com/content/search/scopus`
- **Configuration Variables:** `SCOPUS_API_KEY` (Elsevier institutional license key)
- **Status:** `IMPLEMENTED_PENDING_CREDENTIALS`
- **Capabilities Implemented:**
  - Queries author works by Scopus Author ID (`AU-ID(...)`).
  - Normalizes Scopus JSON responses into `ResearchPaper` records.
- **Resilience & Fallback:**
  - When `SCOPUS_API_KEY` is empty, raises informative `ValueError` cleanly communicated to the user or CLI: *"SCOPUS_API_KEY is not configured; Scopus import requires an Elsevier licence key."*
  - Malformed records skipped automatically.
- **Verification Evidence:** `tests/test_import.py::test_scopus_unconfigured_error`.

---

### 2.6 Google Scholar / SerpAPI Integration
- **Primary Code Modules:** `papers/scholar_service.py`, `dashboard/management/commands/sync_latest_research.py`
- **Configuration Variables:** `SERPAPI_API_KEY`, `SCHOLAR_API_PROVIDER`, `SCHOLAR_API_TIMEOUT`
- **Status:** `FULLY_FUNCTIONAL` (with open scholarly fallback search)
- **Capabilities Implemented:**
  - Discovers high-impact papers, citation counts, and author networks.
  - Fallback engine uses resilient scholarly queries to populate research trends and marquee announcements even when SerpAPI quota is exhausted.
- **Verification Evidence:** `tests/test_google_scholar_integration.py`.

---

### 2.7 Institutional OAI-PMH Harvesting
- **Primary Code Modules:** `papers/importers.py` (Architecture specification in `docs/p08-modules.md`)
- **Status:** `PARTIALLY_IMPLEMENTED`
- **Assessment:**
  - Core publication register stores external sources (`ORCID`, `CROSSREF`, `SCOPUS`, `MANUAL`).
  - OAI-PMH Dublin Core mapping is specified in architecture documentation; institutional live harvest endpoint is planned as an extension hook.
- **Recommendation:** Document clear OAI-PMH endpoint configuration instructions in production manual.

---

### 2.8 RFC 5545 iCalendar (`.ics`) Integration
- **Primary Code Modules:** `facilities/views.py::booking_calendar_ics`
- **Endpoint:** `GET /facilities/bookings/<pk>/calendar.ics`
- **Status:** `FULLY_FUNCTIONAL`
- **Capabilities Implemented:**
  - Exports approved and pending facility bookings as standard `.ics` calendar event files.
  - Computes exact UTC `DTSTART` and `DTEND` timestamps from PostgreSQL `during` range.
  - Generates unique `UID`, `SUMMARY`, `DESCRIPTION`, and `LOCATION` tags.
  - Direct one-click import into Google Calendar, Apple Calendar, and Microsoft Outlook.
- **Verification Evidence:** `tests/test_p08_gaps.py::test_booking_calendar_ics`.

---

### 2.9 Client-Side Visualization Libraries (Chart.js & Cytoscape.js)
- **Chart.js:**
  - Loaded via CDN in `templates/base.html`.
  - Powers portfolio novelty radar, research trends, departmental analytics, and facility utilization.
  - Status: `FULLY_FUNCTIONAL`.
- **Cytoscape.js 3.28.1:**
  - Loaded strictly on `/collaboration/graph/` (`templates/collaboration/graph.html`) to avoid global bundle bloat.
  - Visualizes co-authorship networks, project affiliations, and suggested pairings.
  - Includes full accessible tabular HTML fallback for screen readers and offline environments.
  - Status: `FULLY_FUNCTIONAL`.

---

## 3. Integration Hardening Plan

1. **Environment Configuration Helper:** Provide automated `.env` verification on startup; notify administrators if optional integrations (OpenAI, Scopus, Google OAuth) are absent while ensuring zero server degradation.
2. **Reverse Proxy SSL Header Alignment:** Ensure `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` and dynamic redirect URI generation prevent OAuth redirect mismatches in containerized deployments.
3. **Resilient Network Timeouts:** Ensure all external HTTP requests have explicit connection and read timeouts (`timeout=10` or `15`) to prevent worker starvation during upstream outages.
