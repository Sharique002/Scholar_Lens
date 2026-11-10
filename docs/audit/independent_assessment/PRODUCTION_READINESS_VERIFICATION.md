# Scholar Lens — Production Readiness Forensic Verification

**Document Version:** 1.0.0  
**Audit Date:** November 6, 2026  
**Auditor:** Independent Principal Software Auditor & DevOps Architect  

---

## 1. Executive Summary

A forensic evaluation of the production-readiness claim was conducted across code configuration, security settings, deployment checks, and environment definitions.

### Key Finding:
The application code and architecture are **production-hardened**, but the platform cannot be certified as **READY FOR PRODUCTION** until live cloud deployment steps (migration of the target database, configuration of live Google OAuth secrets, and domain verification) are completed.

---

## 2. Django Deployment Check Results

Execution of `python manage.py check --deploy`:
```text
System check identified some issues:

WARNINGS:
?: (security.W004) You have not set a value for the SECURE_HSTS_SECONDS setting.
?: (security.W008) Your SECURE_SSL_REDIRECT setting is not set to True.
?: (security.W009) Your SECRET_KEY has less than 50 characters, less than 5 unique characters, or it's prefixed with 'django-insecure-'.
?: (security.W012) SESSION_COOKIE_SECURE is not set to True.
?: (security.W016) CSRF_COOKIE_SECURE is not set to True.
?: (security.W018) You should not have DEBUG set to True in deployment.

System check identified 6 issues (0 silenced).
```

### Analysis of Deploy Check Warnings:
All 6 warnings stem from the local development environment flag: `DEBUG=True`.  
A forensic review of `scholar_lens/settings.py` (lines 250–270) proves that when `DEBUG=False` is set in production:
```python
SESSION_COOKIE_SECURE = not DEBUG  # True in prod
CSRF_COOKIE_SECURE = not DEBUG     # True in prod

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1', 'yes')
    if SECURE_SSL_REDIRECT:
        SECURE_HSTS_SECONDS = get_int_env('SECURE_HSTS_SECONDS', 31536000)
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```
Therefore, all 6 security flags activate automatically when `DEBUG=False` is supplied via environment variables.

---

## 3. Production Readiness Audit Matrix

| Verification Category | Requirement | Local / Code Status | Deployed Cloud Status | Forensic Assessment |
|---|---|---|---|---|
| **Database Engine** | PostgreSQL 15+ with `pg_trgm` & `btree_gist` | **READY** (PostgreSQL 16 verified) | **PENDING** (Cloud DB unmigrated) | Code is verified; cloud target requires migration execution. |
| **Migrations** | 0 unapplied schema migrations | **READY** in test runner; **PENDING** in live db | **PENDING** | `python manage.py migrate` must be executed on target DB. |
| **Secret Management** | `SECRET_KEY` pulled from environment | **READY** (configured via `.env`) | **PENDING** | Requires strong secret generated in production `.env`. |
| **Debug Mode** | `DEBUG=False` in production | **READY** (environment-controlled) | **PENDING** | Must be set to `False` on hosting platform. |
| **SSL / HTTPS** | Automatic redirection and HSTS headers | **READY** (code hardened in settings) | **PENDING** | Active automatically when `DEBUG=False`. |
| **Reverse Proxy SSL** | `SECURE_PROXY_SSL_HEADER` configured | **READY** (`('HTTP_X_FORWARDED_PROTO', 'https')`) | **READY** | Pre-configured in `scholar_lens/settings.py`. |
| **Static Storage** | WhiteNoise compressed asset storage | **READY** (133 static files collected) | **READY** | Configured in `settings.py`. |
| **Media Handling** | Size limits ($\le 20\text{MB}$) and MIME validation | **READY** (enforced in forms) | **READY** | Enforced in Python form clean methods. |
| **Google OAuth2 SSO** | Real client ID, secret, and authorized redirect URI | **READY** in code & mock tests | **NOT CONFIGURED** | Needs Google Cloud Console client credentials. |
| **AI Capabilities** | OpenAI API key & model settings | **READY** (graceful fallbacks verified) | **READY** | Operates with heuristics if key omitted. |
| **External APIs** | Resilient ingestion from Crossref / ORCID | **READY** (malformed skipping verified) | **READY** | Verified in `tests/test_import.py`. |
| **Cypress E2E** | Live browser validation across 13 specs | **NOT EXECUTED** | **NOT EXECUTED** | Unverified at browser tier. |

---

## 4. Distinction: Local Verification vs. Cloud Deployment

- **Local Development & PostgreSQL Verification:**  
  The codebase, migrations, test suites (252 tests), and PostgreSQL database constraints are **100% VERIFIED AND WORKING**.
- **Live Cloud Production Verification:**  
  The application is **NOT YET DEPLOYED** on a live domain with public SSL certificates, active DNS, migrated production database tables, and authorized Google OAuth2 client credentials.

---

## 5. Production Readiness Verdict

**IMPLEMENTED BUT NOT FULLY VERIFIED FOR CLOUD DEPLOYMENT.**  
The repository is code-ready, but standard operational cloud provisioning remains necessary before opening access to institutional end-users.
