# Scholar Lens — Environment Configuration Reference & Secrets Management Runbook

**Stage 6: Institutional Deployment Preparation & Production Infrastructure Readiness**  
**Document ID:** `docs/stage6/ENVIRONMENT_CONFIGURATION.md`  
**Version:** 1.0.0  
**Target Environments:** Staging (`staging-scholar-lens.university.edu`) & Production (`scholar-lens.university.edu`)  

---

## 1. Executive Summary & Purpose

This document provides the definitive, audit-verified environment configuration reference for the Scholar Lens institutional research platform. It catalogs every runtime variable consumed by the application, defines explicit configuration profiles for staging and production environments, and establishes cryptographic secret management and rotation procedures required for institutional security compliance.

---

## 2. Exhaustive Environment Variable Catalog

### 2.1. Core Application Variables

| Variable Name | Required | Default / Fallback | Type | Description & Operational Impact |
| :--- | :--- | :--- | :--- | :--- |
| `SECRET_KEY` | **YES** | *Insecure development key* | String (min 50 chars) | Cryptographic salt used for cryptographic signing, session signatures, and CSRF token verification. **Must be unique and randomized per environment.** |
| `DEBUG` | **YES** | `True` | Boolean (`True`/`False`) | Toggles Django debug mode. **MUST be `False` in staging and production.** When `False`, enables strict security middleware, HTTPS enforcement, and generic 500 error pages. |
| `ALLOWED_HOSTS` | **YES** | `localhost,127.0.0.1` | Comma-delimited list | Host/domain names that this Django instance is permitted to serve. Protects against HTTP Host Header poisoning attacks. |
| `CSRF_TRUSTED_ORIGINS` | **YES** | Auto-inferred defaults | Comma-delimited URLs | Fully qualified origins (e.g. `https://scholar-lens.university.edu`) permitted to perform unsafe HTTP requests (POST, PUT, DELETE). Required by Django 4+ for HTTPS forms. |
| `DATABASE_URL` | **YES** | None (`sqlite3` fallback) | PostgreSQL URI | Primary database connection string in the format: `postgres://<user>:<password>@<host>:<port>/<dbname>`. Parsed by `dj-database-url` with connection pooling enabled (`conn_max_age=600`, `conn_health_checks=True`). |
| `TIME_ZONE` | NO | `UTC` | String (IANA TZ) | Institutional timezone for database storage and localized timestamps (default: `UTC`). |
| `SITE_NAME` | NO | `Scholar Lens` | String | Institutional platform brand name rendered in navigation bars, page titles, and system communications. |
| `SITE_URL` | **YES** | `http://localhost:8000` | Full URL | Canonical external origin of the deployment used to synthesize fully qualified OAuth return paths and link generation. |

### 2.2. Security & HTTP Hardening Variables

When `DEBUG=False`, Scholar Lens activates rigorous security headers and SSL transport enforcement.

| Variable Name | Required | Production Value | Type | Security & Protocol Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `SECURE_SSL_REDIRECT` | NO | `True` | Boolean | Directs all unencrypted HTTP requests to HTTPS with a 301 Permanent Redirect. Set to `True` behind an SSL-terminating reverse proxy. |
| `SESSION_COOKIE_SECURE` | NO | `True` | Boolean | Marks session cookies with the `Secure` flag, preventing browser transmission over unencrypted HTTP. |
| `CSRF_COOKIE_SECURE` | NO | `True` | Boolean | Marks CSRF protection cookies with the `Secure` flag. |
| `SECURE_HSTS_SECONDS` | NO | `31536000` (1 year) | Integer (seconds) | Sends `Strict-Transport-Security` header to instruct modern browsers to enforce HTTPS for all subsequent requests. |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | NO | `True` | Boolean | Enforces HSTS policies across all subdomains. |
| `SECURE_HSTS_PRELOAD` | NO | `True` | Boolean | Authorizes inclusion in Chrome/Firefox preloaded HSTS domain lists. |
| `SECURE_CONTENT_TYPE_NOSNIFF` | Hardcoded | `True` | Boolean | Emits `X-Content-Type-Options: nosniff` to eliminate MIME-type confusion vulnerabilities. |
| `X_FRAME_OPTIONS` | Hardcoded | `DENY` | String | Prevents framing of all application pages to neutralize clickjacking attacks. |
| `SECURE_PROXY_SSL_HEADER` | Hardcoded | `('HTTP_X_FORWARDED_PROTO', 'https')` | Tuple | Signals to Django that the request originated via HTTPS when reverse proxy terminates TLS. |

### 2.3. Authentication & Single Sign-On (Google OAuth 2.0 / OIDC)

| Variable Name | Required | Example Format | Security & Operational Details |
| :--- | :--- | :--- | :--- |
| `GOOGLE_CLIENT_ID` | **YES** | `*.apps.googleusercontent.com` | Public OAuth 2.0 client credential assigned in the Google Cloud Console. |
| `GOOGLE_CLIENT_SECRET` | **YES** | Cryptographic token | Confidential client secret used in authorization code exchange on the backend. **Never expose to client or browser.** |
| `GOOGLE_OAUTH_REDIRECT_URI` | **YES** | `https://domain/accounts/google/callback/` | Exact, canonical OAuth callback endpoint. Must match the Authorized Redirect URI in Google Cloud Console byte-for-byte. |

### 2.4. AI & Scholarly Integration Variables

| Variable Name | Required | Default / Fallback | Operational Impact & Fallback Mechanism |
| :--- | :--- | :--- | :--- |
| `OPENAI_API_KEY` | Conditional | Empty string | OpenAI API bearer key for embeddings and RAG evaluation. When blank, the AI Engine seamlessly degrades to deterministic keyword and rule-based evaluation. |
| `OPENAI_MODEL` | NO | `gpt-4o-mini` | Cost-effective LLM selected for paper summarization and proposal gap analysis. |
| `OPENAI_EMBEDDING_MODEL` | NO | `text-embedding-3-small` | 1536-dimension embedding model for publication vector representations. |
| `SCOPUS_API_KEY` | NO | Empty string | Elsevier institutional developer key for Scopus metadata enrichment. When omitted, uses standard Crossref/PubMed API harvesting. |
| `SERPAPI_API_KEY` | NO | Empty string | Commercial Google Scholar API search wrapper. Fallback to direct DOI parsing when blank. |
| `SCHOLAR_API_TIMEOUT` | NO | `10` (seconds) | HTTP request socket timeout for external scholarly indexing queries. |
| `SCHOLAR_MAX_RESULTS` | NO | `5` | Maximum citation results fetched per automated search pass. |

### 2.5. Storage, Media & P08 Functional Parameters

| Variable Name | Required | Default | Rationale |
| :--- | :--- | :--- | :--- |
| `MAX_UPLOAD_SIZE_MB` | NO | `20` | Maximum single-file upload size (MB) for researcher CVs, paper PDFs, and project milestone attachments. Enforced in form validators and Django memory buffers. |
| `FUNDING_ALERT_DAYS` | NO | `30,14,7,1` | Day thresholds before grant proposal deadline triggering institutional notification alerts. |
| `MILESTONE_AT_RISK_DAYS` | NO | `7` | Threshold in days within which a project milestone with low completion percentage is flagged as "At Risk". |
| `MILESTONE_AT_RISK_PROGRESS`| NO | `50` (%) | Minimum completion percentage required within the warning window to avoid "At Risk" status. |
| `E2E` | NO | `False` | Test bypass flag enabling deterministic fixture accounts. **Strictly prohibited in production.** |

---

## 3. Environment Profiles

### 3.1. Staging Environment Profile (`staging.env`)

Staging mirrors production security policies while permitting isolated testing and staging-specific callback endpoints.

```ini
# ==============================================================================
# SCHOLAR LENS STAGING CONFIGURATION PROFILE
# Environment: Staging (UAT & Pre-Production Verification)
# Hostname: staging-scholar-lens.university.edu
# ==============================================================================

# Core Application
SECRET_KEY=stg_sec_k982f1b40283c847a6109d736a592e01b4c9e821f04b2a3c
DEBUG=False
SITE_NAME="Scholar Lens (Staging)"
SITE_URL=https://staging-scholar-lens.university.edu
TIME_ZONE=UTC
ALLOWED_HOSTS=staging-scholar-lens.university.edu,10.0.1.20
CSRF_TRUSTED_ORIGINS=https://staging-scholar-lens.university.edu

# Database (PostgreSQL 16 Staging Dedicated Instance)
DATABASE_URL=postgres://scholar_lens_stg:K8x#m9Qv!L2z@db-staging.internal:5432/scholar_lens_stg

# Security & SSL
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=False

# Authentication (Staging OAuth Credentials)
GOOGLE_CLIENT_ID=<YOUR_STAGING_GOOGLE_CLIENT_ID>
GOOGLE_CLIENT_SECRET=<YOUR_STAGING_GOOGLE_CLIENT_SECRET>
GOOGLE_OAUTH_REDIRECT_URI=https://staging-scholar-lens.university.edu/accounts/google/callback/

# AI & External APIs
OPENAI_API_KEY=sk-proj-stg-OpenAIKeyExampleWithLimitedBudget12345
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
SCOPUS_API_KEY=
SERPAPI_API_KEY=

# File Limits & Functional Thresholds
MAX_UPLOAD_SIZE_MB=20
FUNDING_ALERT_DAYS=30,14,7,1
MILESTONE_AT_RISK_DAYS=7
MILESTONE_AT_RISK_PROGRESS=50
E2E=False
```

---

### 3.2. Production Environment Profile (`production.env`)

```ini
# ==============================================================================
# SCHOLAR LENS PRODUCTION CONFIGURATION PROFILE
# Environment: Production
# Hostname: scholar-lens.university.edu
# ==============================================================================

# Core Application
SECRET_KEY=prod_sec_8e72c91a03f47b2c95e10984a6c2d3b487e9120485a6b7c8
DEBUG=False
SITE_NAME="Scholar Lens"
SITE_URL=https://scholar-lens.university.edu
TIME_ZONE=UTC
ALLOWED_HOSTS=scholar-lens.university.edu,10.0.2.15
CSRF_TRUSTED_ORIGINS=https://scholar-lens.university.edu

# Database (PostgreSQL 16 High-Availability Cluster with Read Replica)
DATABASE_URL=postgres://scholar_lens_prod:P#9xV!8qW@db-prod.internal:5432/scholar_lens_prod

# Security & SSL
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Authentication (Production Google OAuth App)
GOOGLE_CLIENT_ID=<YOUR_PRODUCTION_GOOGLE_CLIENT_ID>
GOOGLE_CLIENT_SECRET=<YOUR_PRODUCTION_GOOGLE_CLIENT_SECRET>
GOOGLE_OAUTH_REDIRECT_URI=https://scholar-lens.university.edu/accounts/google/callback/

# AI & External APIs (Institutional Enterprise Keys)
OPENAI_API_KEY=sk-proj-prod-EnterpriseOpenAIKeyValidatedAccount88
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
SCOPUS_API_KEY=elsevier_prod_institutional_api_token
SERPAPI_API_KEY=serp_prod_live_search_key_492018

# File Limits & Functional Thresholds
MAX_UPLOAD_SIZE_MB=20
FUNDING_ALERT_DAYS=30,14,7,1
MILESTONE_AT_RISK_DAYS=7
MILESTONE_AT_RISK_PROGRESS=50
E2E=False
```

---

## 4. Institutional Secrets Management & Rotation Policy

### 4.1. Storage & Secret Injection Standard

1. **No Secret in Version Control:**  
   Plaintext `.env` files are explicitly excluded via `.gitignore`. Committing credentials, passwords, or private keys results in an immediate security incident and revoked keys.
2. **Secrets Manager Integration:**  
   In institutional production environments, secrets must be stored in an audited key-management store:
   - **HashiCorp Vault**, **AWS Secrets Manager**, or **GCP Secret Manager**.
   - Container environments inject secrets dynamically at container startup as environment variables via orchestration secrets (Docker Secrets, systemd EnvironmentFile with permissions `chmod 600 root:appuser`).

### 4.2. Cryptographic Key Generation Procedures

To generate cryptographically secure values for `SECRET_KEY` and database passwords:

```bash
# Generate 64-character URL-safe Django SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Generate 32-character high-entropy database password
openssl rand -base64 32
```

### 4.3. Key Rotation Protocols

| Credential Type | Rotation Frequency | Rotation Procedure & Zero-Downtime Strategy |
| :--- | :--- | :--- |
| `SECRET_KEY` | Annually or upon breach suspicion | **Impact:** Invalidates active browser sessions. Plan during scheduled maintenance window (02:00-04:00 AM). Update secret store and perform rolling restart of Gunicorn worker processes. |
| `DATABASE_URL` Password | Semi-annually | 1. Create secondary DB user or update password using `ALTER USER scholar_lens WITH PASSWORD 'new';`<br>2. Update secret store.<br>3. Perform rolling application reload to cycle database connection pools. |
| `GOOGLE_CLIENT_SECRET` | Annually | 1. Generate secondary Client Secret in Google Cloud Console.<br>2. Deploy new secret to application.<br>3. Verify login workflows in staging.<br>4. Delete deprecated secret in Google Cloud Console. |
| `OPENAI_API_KEY` | Every 90 days | 1. Issue new API key in OpenAI Organization dashboard.<br>2. Update environment variable in secret store.<br>3. Reload application service.<br>4. Revoke previous key after 24 hours. |

---

## 5. Security & Deployment Verification Checklist

Prior to launching staging or production, execute the automated configuration verification:

```bash
# 1. Verify Django deployment configuration passes all 0 security warnings
python manage.py check --deploy

# 2. Verify database connection string resolves and connects
python -c "import django; django.setup(); from django.db import connection; connection.cursor().execute('SELECT 1;'); print('Database connectivity verified!')"

# 3. Verify static assets compile cleanly
python manage.py collectstatic --dry-run --noinput
```

All 3 checks must return status code `0` with zero warnings before traffic is directed to the instance.
