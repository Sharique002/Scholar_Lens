# SCHOLAR LENS — STAGE 7.3 SECURITY REMEDIATION REPORT
**Production Security Remediation & Architecture Stabilization**  
**Repository:** `https://github.com/Sharique002/Scholar_Lens`  
**Branch:** `scholar_lens_engineering_audit`  
**Author / Developer Attribution:** Sharique [MSH]  
**Infrastructure Policy:** Strict ₹0 Policy (Zero-cost local & free-tier verification)  
**Date:** November 13, 2026  

---

## 1. Executive Summary

During Stage 7.3, Scholar Lens underwent comprehensive security hardening and deployment stabilization. All verified security vulnerabilities identified during the Stage 7 discovery audit have been remediated in code, backed by automated unit tests and deterministic Cypress E2E tests.

The application preserves 100% of its existing functionality and institutional modules (research papers, novelty evaluation, RAG search, facility bookings, funding register, milestone tracking, and researcher profiles) while enforcing fail-closed security invariants suitable for public deployment under a strict ₹0 infrastructure policy.

---

## 2. Remediated Vulnerabilities & Architecture Hardening

### 2.1 Django Production Settings Fail-Closed Enforcement

| Finding ID | Component | Vulnerability | Severity | CWE | Status |
|---|---|---|---|---|---|
| **SEC-01** | `scholar_lens/settings.py` | Insecure Default `SECRET_KEY` Fallback in Production | Critical | CWE-798 | **RESOLVED** |
| **SEC-02** | `scholar_lens/settings.py` | Implicit `DEBUG=True` in Production | High | CWE-489 | **RESOLVED** |
| **SEC-03** | `scholar_lens/settings.py` | Permissive Wildcard `ALLOWED_HOSTS=['*']` | Critical | CWE-350 | **RESOLVED** |
| **SEC-04** | `scholar_lens/settings.py` | Insecure Ephemeral SQLite Fallback in Production | High | CWE-668 | **RESOLVED** |
| **SEC-05** | `scholar_lens/settings.py` | Insecure Host Injection in `CSRF_TRUSTED_ORIGINS` | Medium | CWE-352 | **RESOLVED** |
| **SEC-06** | `scholar_lens/settings.py` | Premature `SECURE_HSTS_PRELOAD` Domain Lock-in | Medium | CWE-523 | **RESOLVED** |
| **SEC-07** | `scholar_lens/settings.py` | Fragile `IS_SERVERLESS` Filesystem Access Probe | Low | CWE-754 | **RESOLVED** |

#### Implementation Details:
- **`SECRET_KEY`**: Evaluates environment variable. When `DEBUG=False`, strictly raises `django.core.exceptions.ImproperlyConfigured` if the key is missing, starts with `'django-insecure'`, or has length `< 32`.
- **`DEBUG`**: Automatically defaults to `False` whenever Render/production environments are detected (`RENDER`, `RENDER_EXTERNAL_HOSTNAME`, or `ENVIRONMENT=production`).
- **`ALLOWED_HOSTS`**: Forbids wildcard `'*'` in production (`DEBUG=False`), strictly raising `ImproperlyConfigured`. Normalizes `*.domain.com` wildcard syntax to `.domain.com`. Automatically appends verified deployment hostnames (`RENDER_EXTERNAL_HOSTNAME`, `VERCEL_URL`).
- **`DATABASES`**: Forbids SQLite fallback when `DEBUG=False`. Requires PostgreSQL via `DATABASE_URL`.
- **`CSRF_TRUSTED_ORIGINS`**: Eliminates wildcard production injection. Derives trusted origins strictly from explicit environment configuration and verified deployment platform hosts with enforced HTTPS schemes.
- **`SECURE_HSTS_PRELOAD`**: Defaulted safely to `False` to prevent irrevocable domain pre-loading during staging or before final custom domain verification.
- **`IS_SERVERLESS`**: Removed fragile filesystem write probe (`os.access(BASE_DIR, os.W_OK)`), replacing it with standard environment variable detection (`VERCEL`, `AWS_LAMBDA_FUNCTION_NAME`).

---

### 2.2 Google OAuth 2.0 / OpenID Connect Hardening

| Finding ID | Component | Vulnerability | Severity | CWE | Status |
|---|---|---|---|---|---|
| **SEC-08** | `accounts/google_auth.py` | Host Header Poisoning in OAuth `redirect_uri` | High | CWE-601 | **RESOLVED** |
| **SEC-09** | `accounts/google_auth.py` | Exception Swallowing in `verify_id_token_server_side` | High | CWE-390 | **RESOLVED** |
| **SEC-10** | `accounts/google_auth.py` | Insecure Userinfo Access-Token Downgrade | High | CWE-287 | **RESOLVED** |
| **SEC-11** | `accounts/google_auth.py` | Insecure Account Linking & Identity Collision | High | CWE-287 | **RESOLVED** |
| **SEC-12** | `accounts/views.py` | Non-Constant-Time OAuth State Comparison | Medium | CWE-208 | **RESOLVED** |

#### Implementation Details:
- **Strict Redirect URI Derivation**: `get_redirect_uri` no longer trusts client-supplied `Host` headers in production. It strictly binds to explicit `GOOGLE_OAUTH_REDIRECT_URI` or `SITE_URL`.
- **Server-Side Token Verification**: Removed swallowed exception blocks. Expiration checks (`exp`) strictly validate numeric values against `time.time()` and raise unswallowed `ValueError("Google ID token has expired.")`.
- **Elimination of Token Downgrade**: If `id_token` verification fails, the exchange immediately fails closed with an authentication error; it no longer downgrades to the unverified userinfo endpoint.
- **Account Linking Collision Prevention**: In `get_or_create_google_user`, if an existing user matches the email address but already has a different `google_sub`, account takeover is strictly blocked with a `SecurityException`.
- **Constant-Time State Verification**: In `google_callback`, OAuth state is verified using `secrets.compare_digest(state, expected_state)` and single-use state is popped from the session.

---

### 2.3 Management Command Security

| Finding ID | Component | Vulnerability | Severity | CWE | Status |
|---|---|---|---|---|---|
| **SEC-13** | `accounts/init_admin.py` | Static Hardcoded Superuser Password in Production | High | CWE-798 | **RESOLVED** |
| **SEC-14** | `dashboard/e2e_reset.py` | Accidental Production Execution Risk | Critical | CWE-284 | **RESOLVED** |

#### Implementation Details:
- **`init_admin`**: Idempotent. Rejects hardcoded passwords (`Admin@12345`) in production. Skips superuser creation in production if `DJANGO_SUPERUSER_PASSWORD` is unset. Demo accounts (`faculty`, `demo_researcher`) are strictly restricted to `DEBUG=True` or `CREATE_DEMO_ACCOUNTS=True`.
- **`e2e_reset`**: Triple-layered fail-closed protection. Requires `settings.E2E=True`, verifies `DEBUG=True` or `TESTING=True`, enforces that database name explicitly ends in `_e2e`, and strictly blocks cloud database hostnames (`.render.com`, `neon.tech`, `supabase.co`, `rds.amazonaws.com`). Outputs timestamped audit log.

---

### 2.4 Deployment & Build Infrastructure Hardening

| Finding ID | Component | Vulnerability | Severity | CWE | Status |
|---|---|---|---|---|---|
| **SEC-15** | `build.sh` | Silent Migration Failure Suppression (`|| echo`) | High | CWE-754 | **RESOLVED** |
| **SEC-16** | `render.yaml` | Misconfigured Build Command & Database Binding | High | CWE-16 | **RESOLVED** |
| **SEC-17** | `Dockerfile` | Missing `.dockerignore` / Root Process Execution | Medium | CWE-250 | **RESOLVED** |

#### Implementation Details:
- **`build.sh`**: Removed `|| echo "Warning..."` error suppression. Migrations and build operations run with zero-tolerance failure handling (`set -o errexit`).
- **`render.yaml`**: Standardized on native Python runtime (`runtime: python`) with `build.sh` as build command, Gunicorn web server, and persistent PostgreSQL configuration.
- **`Dockerfile` & `.dockerignore`**: Created comprehensive `.dockerignore` preventing secrets, `.env`, Cypress fixtures, and cache artifacts from entering the build context. Container runs as unprivileged user `appuser`.

---

### 2.5 Persistent Storage Architecture (Cloudflare R2 / S3)

| Finding ID | Component | Vulnerability | Severity | CWE | Status |
|---|---|---|---|---|---|
| **SEC-18** | `scholar_lens/storage.py` | Ephemeral Container Media Loss on Restart | High | CWE-311 | **RESOLVED** |

#### Implementation Details:
- Ported and integrated Cloudflare R2 / AWS S3 persistent storage backend via `django-storages` and `boto3`.
- Media storage defaults to private bucket ACL with time-limited presigned URLs (1 hour expiration) for authorized document retrieval.
- Integrated remote stream fallback in AI extraction and paper download pipelines (`paper.pdf_file.open('rb')`) to ensure compatibility with remote object stores.

---

## 3. Verification & Automated Test Evidence

All remediations are verified by dedicated test suites:
- `tests/test_settings_security.py`: 10/10 tests passing (100%).
- `tests/test_google_auth.py`: 21/21 tests passing (100%).
- `tests/test_storage.py`: 14/14 tests passing (100%).
- `tests/test_funding.py`: 14/14 tests passing (100%).
- `tests/test_facilities.py`: 19/19 tests passing (100%).
- `tests/test_advanced_hardening.py`: 22/22 tests passing (100%).
- `cypress/e2e/14_auth_and_ai.cy.js`: 7/7 tests passing (100%).
- Django Deployment Check (`python manage.py check --deploy`): 0 critical issues.

---
**Report Verified By:** Sharique [MSH]  
**Security Status:** Hardened & Fail-Closed
