# Scholar Lens — Google OAuth & Authentication Forensic Verification

**Document Version:** 1.0.0  
**Audit Date:** November 6, 2026  
**Auditor:** Independent Principal Software Auditor & Security Engineer  

---

## 1. Executive Summary

A forensic evaluation of the Google OAuth2 / OpenID Connect single sign-on (SSO) architecture was conducted by inspecting:
- `accounts/google_auth.py` (Core OAuth & OIDC verification service)
- `accounts/views.py` (`google_login_view`, `google_callback_view`, `google_mock_view`)
- `templates/accounts/login.html` & `templates/accounts/register.html`
- `tests/test_google_auth.py` (14 automated test cases)

---

## 2. Four-Level Verification Classification

To eliminate ambiguity between automated mock testing and live production readiness, authentication verification is partitioned into four distinct tiers:

### Tier A: Mocked OAuth Unit Tests
- **Status:** **PASS (100% Verified)**
- **Evidence:** `tests.test_google_auth` (Tests 1–7)
- **Verified Capabilities:**
  - `is_google_auth_configured()` accurately detects presence of client ID and secret.
  - Server-side ID token claim validation correctly parses audience (`aud`), issuer (`iss`), expiration (`exp`), and email verification status (`email_verified`).
  - Cryptographic token verification gracefully falls back to Google's `tokeninfo` endpoint when `google-auth` library encounters formatting exceptions.
  - Token audience mismatch raises `ValueError("ID token audience mismatch")`.
  - Unverified Google emails raise `ValueError("Google account email address is not verified")`.
  - Expired ID tokens raise `ValueError("Google ID token has expired")`.

### Tier B: Application View Integration Tests
- **Status:** **PASS (100% Verified)**
- **Evidence:** `tests.test_google_auth` (Tests 8–14)
- **Verified Capabilities:**
  - `google_login_view` redirects to Google's authorization endpoint (`https://accounts.google.com/o/oauth2/v2/auth`) with random 32-byte cryptographic state parameter.
  - `google_callback_view` validates matching `state` token from session; mismatched state returns an error message and redirects to login (CSRF protection).
  - Open redirect attacks via `?next=` parameter are blocked; unapproved external hosts are sanitized to `dashboard:home`.
  - User cancellation (`?error=access_denied`) is gracefully intercepted without unhandled exceptions.
  - New user provisioning creates a `User`, an associated `UserProfile` with linked immutable `google_sub`, and a `ResearcherProfile`.
  - Returning user is recognized by immutable `google_sub`, even if their email address changes.
  - Pre-existing user registered via traditional password has their account safely linked to their `google_sub` upon first Google sign-in.
  - Session creation logs an append-only `ResearchActivity` record with action type `'LOGIN'`.

### Tier C: Live Browser Authorization Flow
- **Status:** **NOT EXECUTED / UNVERIFIED**
- **Evidence:** No live browser interaction executed against Google's live identity servers.
- **Reason:** Requires an interactive desktop browser session, a real Google account with active MFA, and live client secrets.

### Tier D: Production Domain Deployment Verification
- **Status:** **NOT EXECUTED / UNVERIFIED**
- **Evidence:** `.env.example` contains placeholder credentials (`your-google-client-id.apps.googleusercontent.com`).
- **Reason:** Full production-domain OAuth requires:
  1. An approved OAuth consent screen in Google Cloud Console.
  2. Authorized JavaScript origins matching the live domain (e.g. `https://scholar-lenss.vercel.app`).
  3. Authorized redirect URIs configured matching `https://scholar-lenss.vercel.app/accounts/google/callback/`.
  4. Real client ID and secret populated in production environment variables.

---

## 3. Production Hardening Audit

The view implementation in `accounts/views.py` was inspected for production hardening rules:

```python
def google_mock_view(request):
    """Mock Google sign-in for development, testing, and CI environments."""
    if not settings.DEBUG:
        messages.error(request, "Mock authentication is disabled in production.")
        return redirect('accounts:login')
```

1. **Mock Sign-In Gate:** The mock sign-in endpoint is strictly disabled when `settings.DEBUG = False`. In production, any attempt to access `/accounts/google/mock/` triggers an error message and redirects to the standard login view.
2. **Reverse Proxy SSL Support:** In `accounts/google_auth.py`, `get_redirect_uri(request)` uses `request.build_absolute_uri()`. Combined with `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` in `settings.py`, the callback URI correctly generates `https://` behind production load balancers and reverse proxies (Vercel, Nginx, AWS ALB).

---

## 4. Final Authentication Verdict

- **Code Quality & Architecture:** **VERIFIED (Production-Grade Code)**.
- **Unit & Integration Security:** **PASS (14 / 14 Tests Passing)**.
- **Live Google Cloud Infrastructure:** **UNVERIFIED (Requires production credentials and Google Cloud Console configuration)**.
