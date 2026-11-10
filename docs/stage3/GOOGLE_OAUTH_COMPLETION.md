# Scholar Lens — Google OAuth & Authentication Completion Report
**Stage 3: Engineering Remediation & Integration Verification**  
**Document ID:** `DOC-S3-AUTH-01`  
**Execution Date:** 2026-11-06  
**Status:** FULLY IMPLEMENTED & TEST-VERIFIED (LIVE CLOUD REGISTRATION READY)  

---

## 1. Executive Summary

This report documents the architectural implementation, cryptographic security verification, and automated testing of Google OAuth2 / OpenID Connect authentication in Scholar Lens. 

The implementation uses server-side Authorization Code Flow with OpenID Connect ID token verification (`google-auth` / tokeninfo verification), state CSRF defense, open redirect prevention, session fixation protection, and persistent user matching via Google Subject ID (`google_sub`).

All 14 automated test scenarios in `tests/test_google_auth.py` pass cleanly (100% success rate on PostgreSQL 16). The system is fully ready for production configuration upon entering live Google Cloud Console credentials into environment variables.

---

## 2. Architecture & Security Specifications

### 2.1 Component Architecture
- **Service Layer:** `accounts/google_auth.py`
  - `is_google_auth_configured()`: Dynamic validation of `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
  - `get_redirect_uri(request)`: Dynamic request-aware URI builder respecting development hosts (`localhost`, `127.0.0.1`) and production domains (`https://scholar-lens.vercel.app/accounts/google/callback/`).
  - `get_google_auth_url(request, next_url)`: Cryptographic state generation (`secrets.token_urlsafe(32)`), session binding, and Google Auth endpoint URL construction.
  - `verify_id_token_server_side(id_token, expected_client_id)`: Multi-layer JWT validation using Google's public keys via `google.oauth2.id_token.verify_oauth2_token`.
  - `exchange_code_for_user_info(code, redirect_uri)`: Server-to-server token exchange with `https://oauth2.googleapis.com/token`.
  - `get_or_create_google_user(user_info)`: Resilient user matching and automated account provisioning.
- **View Layer:** `accounts/views.py`
  - `GoogleLoginView`: Initiates flow or displays helpful warning if client credentials are not configured.
  - `GoogleCallbackView`: Processes callback, checks for user denial/errors, validates state token, exchanges code, securely logs in user, and safely redirects.
- **Data Layer:** `accounts/models.py`
  - `UserProfile.google_sub`: Indexed character field storing the Google unique user identifier (`sub`).

### 2.2 Security Controls Implemented

| Security Vulnerability | Defensive Control | File & Location |
|---|---|---|
| **CSRF / State Manipulation** | Cryptographic random state token (`secrets.token_urlsafe(32)`) stored in signed session, validated on callback. | `accounts/google_auth.py:58`, `accounts/views.py:73` |
| **Token Forgery / Spoofing** | ID token cryptographic signature verification against Google JWKS public keys. | `accounts/google_auth.py:89-97` |
| **Audience Confusion Attack** | Explicit validation that `aud` equals configured `GOOGLE_CLIENT_ID`. | `accounts/google_auth.py:109-111` |
| **Issuer Impersonation** | Explicit validation that `iss` is `accounts.google.com` or `https://accounts.google.com`. | `accounts/google_auth.py:114-116` |
| **Replay Attacks** | Expiration timestamp (`exp`) validated against UTC system time with 10s clock skew window. | `accounts/google_auth.py:119-125` |
| **Unverified Email Hijack** | Enforces `email_verified == True`; rejects unverified accounts. | `accounts/google_auth.py:128-130` |
| **Open Redirect Vulnerability** | Validates target `next` URL using Django's `url_has_allowed_host_and_scheme`. Falls back to `dashboard:index`. | `accounts/views.py:107-111` |
| **Session Fixation** | Enforces `request.session.cycle_key()` upon successful authentication. | `accounts/views.py:101` |
| **Reverse Proxy HTTPS Protocol** | Respects `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` and `USE_X_FORWARDED_HOST = True`. | `scholar_lens/settings.py` |

---

## 3. Account Provisioning & Linking Flow

1. **Step 1: Check `google_sub`**  
   If a `UserProfile` exists with matching `google_sub`, that user is returned immediately. This ensures consistent identity even if the user changes their primary Google email.
2. **Step 2: Check Email Matching**  
   If no user has that `google_sub`, the system searches for an existing `User` with matching email. If found, `user.profile.google_sub` is updated and persisted.
3. **Step 3: Automated Provisioning**  
   If no user exists, a new Django `User` is created:
   - Unique username derived from email or name slug with collision counter.
   - `set_unusable_password()` applied.
   - `UserProfile` created with `role='STUDENT'` (default institutional entry role) and `google_sub` saved.
   - `ResearcherProfile` automatically initialized in `researchers_researcherprofile`.
   - Initial audit activity logged in `ResearchActivity`.

---

## 4. Automated Test Verification Results

All 14 test cases in `tests/test_google_auth.py` were executed against the PostgreSQL 16 database instance:

```text
Creating test database for alias 'default'...
....google.oauth2.id_token verification raised: Wrong number of segments in token: b'dummy_id_token', falling back to tokeninfo endpoint.
..google.oauth2.id_token verification raised: Wrong number of segments in token: b'dummy_id_token', falling back to tokeninfo endpoint.
.google.oauth2.id_token verification raised: Wrong number of segments in token: b'dummy_id_token', falling back to tokeninfo endpoint.
.......
----------------------------------------------------------------------
Ran 14 tests in 6.318s

OK
Destroying test database for alias 'default'...
```

### Complete Test Case Breakdown:

| Test Case Name | Target Behavior | Result |
|---|---|---|
| `test_is_google_auth_configured` | Validates configuration detection when keys are empty vs provided. | **PASS** |
| `test_first_login_creates_user_with_google_sub` | Validates new user creation, password usability, profile creation, and `google_sub`. | **PASS** |
| `test_returning_login_recognized_by_google_sub` | Validates returning user lookup by `google_sub` even if email changes. | **PASS** |
| `test_returning_login_by_email_links_google_sub` | Validates account linking for pre-existing email accounts without duplicate user creation. | **PASS** |
| `test_verify_id_token_google_auth_success` | Validates ID token cryptographic verification via Google auth library mock. | **PASS** |
| `test_verify_id_token_server_side_success` | Validates tokeninfo endpoint fallback verification. | **PASS** |
| `test_verify_id_token_audience_mismatch_rejected` | Validates rejection when `aud` does not match expected client ID. | **PASS** |
| `test_verify_id_token_unverified_email_rejected` | Validates rejection of Google accounts with unverified emails. | **PASS** |
| `test_google_login_redirect_url_and_session_state` | Validates authorization URL generation and state storage in session. | **PASS** |
| `test_google_login_missing_config_returns_warning` | Validates user warning redirect if OAuth credentials are not configured. | **PASS** |
| `test_callback_state_mismatch_rejected` | Validates 400 Bad Request if session state does not match callback state. | **PASS** |
| `test_callback_user_cancelled_redirects_login` | Validates clean error redirect to login page when user clicks cancel at Google prompt. | **PASS** |
| `test_callback_successful_login_and_session` | Validates end-to-end callback execution, login session creation, and redirect. | **PASS** |
| `test_callback_prevents_open_redirect` | Validates prevention of malicious off-site redirects (e.g. `https://evil.com`). | **PASS** |

---

## 5. Google Cloud Console Production Setup Guide

To transition from automated mock verification to live end-user Google authentication in production:

### 5.1 Prerequisites in Google Cloud Console
1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Select or create project `scholar-lens-prod`.
3. Navigate to **APIs & Services > OAuth consent screen**:
   - User Type: **External** (or Internal for institutional Google Workspace).
   - App Name: `Scholar Lens Research Platform`.
   - User support email & Developer contact info: institutional administrator.
   - Scopes: `openid`, `.../auth/userinfo.email`, `.../auth/userinfo.profile`.
4. Navigate to **APIs & Services > Credentials > Create Credentials > OAuth client ID**:
   - Application type: **Web application**.
   - Name: `Scholar Lens Web Client`.
   - **Authorized JavaScript origins:**
     - `http://localhost:8000`
     - `http://127.0.0.1:8000`
     - `https://scholar-lens.vercel.app` (or production domain)
   - **Authorized redirect URIs:**
     - `http://localhost:8000/accounts/google/callback/`
     - `http://127.0.0.1:8000/accounts/google/callback/`
     - `https://scholar-lens.vercel.app/accounts/google/callback/`

### 5.2 Environment Configuration
Add the obtained credentials to `.env` or deployment secrets:
```ini
GOOGLE_CLIENT_ID=<YOUR_GOOGLE_CLIENT_ID>
GOOGLE_CLIENT_SECRET=<YOUR_GOOGLE_CLIENT_SECRET>
GOOGLE_OAUTH_REDIRECT_URI=https://scholar-lens.vercel.app/accounts/google/callback/
```

---

## 6. Verification Status Summary

| Area | Status | Evidence |
|---|---|---|
| Django Code Implementation | Complete | `accounts/google_auth.py`, `accounts/views.py` |
| Security Protections | Complete | CSRF state, JWT signature, Aud/Iss validation, Session cycle |
| Automated Unit & Integration Tests | 14/14 PASS | `tests.test_google_auth` |
| Production Cloud Registration | Ready for Keys | Step-by-step configuration manual completed above |
