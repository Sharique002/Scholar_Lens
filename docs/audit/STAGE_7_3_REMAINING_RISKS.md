# SCHOLAR LENS — STAGE 7.3 REMAINING RISKS & OPERATIONAL CAVEATS
**Risk Assessment, Limitations & Operational Mitigation Playbook**  
**Repository:** `https://github.com/Sharique002/Scholar_Lens`  
**Branch:** `scholar_lens_engineering_audit`  
**Developer Attribution:** Sharique [MSH]  
**Infrastructure Policy:** Strict ₹0 Policy  
**Date:** November 13, 2026  

---

## 1. Executive Risk Assessment

While Stage 7.3 remediated all critical code-level and architecture vulnerabilities, several operational constraints remain due to external platform dependencies and the strict ₹0 infrastructure policy.

This document transparently records these operational realities, their risk levels, and actionable mitigation protocols.

---

## 2. Identified Operational Risks & Mitigations

### 2.1 Google Cloud OAuth Live Production Consent
- **Risk Level**: **Medium** (Configuration / External Dependency)
- **Description**: While Google OAuth 2.0 flow is hardened in code and thoroughly validated across 21 unit tests and Mock SSO, live production authentication requires the project administrator to register an OAuth Client ID in Google Cloud Console, publish the OAuth Consent Screen, and configure the authorized redirect URI (`https://<render-subdomain>.onrender.com/accounts/google/callback/`).
- **Impact**: Until configured in Google Cloud Console, users attempting live Google sign-in in production will receive an OAuth configuration error from Google.
- **Mitigation Protocol**:
  1. Standard username/password registration and login remain 100% operational as primary authentication.
  2. The Google OAuth button is visible, but the application safely fails closed if credentials are unset or invalid.
  3. Step-by-step setup guide is documented in `docs/architecture.md` and `.env.example`.

---

### 2.2 Free-Tier Instance Inactivity Spindown (Render)
- **Risk Level**: **Low to Medium** (User Experience)
- **Description**: Under Render's free tier policy, instances spin down after 15 minutes of inactivity. When a new request arrives, a cold start occurs.
- **Impact**: The initial request after spindown experiences 30–50 seconds of latency while the Python container boots and initializes Gunicorn. Subsequent requests respond in <150ms.
- **Mitigation Protocol**:
  1. A free uptime pinger (e.g., UptimeRobot free tier with 5-minute HTTP HEAD intervals) can be configured to keep the instance warm during active institutional hours.
  2. The frontend loading state and retro design provide visual feedback during initial page load.

---

### 2.3 Serverless Database Inactivity & Connection Limits (Neon / Free Postgres)
- **Risk Level**: **Low**
- **Description**: Free serverless PostgreSQL tiers (such as Neon) auto-suspend compute after 5 minutes of inactivity and impose a limit of 20 concurrent connections.
- **Impact**: A 1–2 second resume pause on the first query after idle. Exceeding 20 concurrent users could exhaust connection slots.
- **Mitigation Protocol**:
  1. Django settings enforce `conn_max_age = 600` and `conn_health_checks = True`, ensuring stale connections are automatically dropped and reconnected without 500 errors.
  2. Gunicorn is configured with 2 workers, bounding database connection pooling well within the 20-connection ceiling.

---

### 2.4 Synchronous Background Workloads (Strict ₹0 Policy)
- **Risk Level**: **Low**
- **Description**: Under the strict ₹0 infrastructure policy, dedicated paid brokers (Redis, RabbitMQ) and separate background worker dynos are not provisioned. Heavy tasks (such as PDF text extraction and embedding generation) run synchronously within HTTP worker threads.
- **Impact**: Uploading extremely large PDFs (>15 MB) or bulk Crossref imports may cause request delays of 5–10 seconds.
- **Mitigation Protocol**:
  1. Client uploads are capped at 20 MB via `MAX_UPLOAD_SIZE_MB`.
  2. Gunicorn request timeout is set to 120 seconds (`--timeout 120`), preventing premature gateway timeouts.
  3. Scheduled jobs (Google Scholar sync, duplicate candidate scanning) can be triggered via free external cron triggers (Render Cron or GitHub Actions scheduled workflows).

---

### 2.5 Third-Party AI API Quotas (OpenAI / SerpAPI)
- **Risk Level**: **Low**
- **Description**: Free-tier OpenAI keys have tight rate limits (3 RPM on free tiers) or credit expiration.
- **Impact**: When quotas are exhausted or API keys are missing, live AI generation and Google Scholar sync will return rate limit or configuration warnings.
- **Mitigation Protocol**:
  1. Scholar Lens enforces graceful degradation: when AI services are unconfigured or fail, the application displays user-friendly warnings (`"AI service not configured"`) without crashing or raising unhandled 500 exceptions.
  2. Institutional workflows (paper browsing, search, author claiming, project tracking, facilities booking) operate completely independently of external AI services.

---

### 2.6 Cloudflare R2 Free Storage Capacity Ceiling
- **Risk Level**: **Informational**
- **Description**: Cloudflare R2 provides 10 GB free storage per month.
- **Impact**: Accommodates ~3,000 to 5,000 standard research papers. Once exceeded, uploads would fail unless paid storage is authorized.
- **Mitigation Protocol**:
  1. Research Office dashboard tracks uploaded volume.
  2. File upload validation rejects non-PDF files and compresses/indexes text efficiently.

---

## 3. Operational Sign-Off

All remaining risks have documented mitigations and do not impede a reliable, zero-cost public pilot deployment.

---
**Risk Assessment Lead:** Sharique [MSH]  
**Architecture Recommendation:** Ready for Staging Validation
