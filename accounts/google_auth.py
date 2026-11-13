"""Google OAuth2 / OpenID Connect Authentication Service for Scholar Lens.

Implements secure Authorization Code Flow with server-side token exchange,
cryptographic OpenID Connect ID token validation via google-auth, and account
provisioning via Google Subject ID (sub).
"""
import logging
import re
import secrets
import time
import urllib.parse
import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
ALLOWED_GOOGLE_ISSUERS = ("accounts.google.com", "https://accounts.google.com")


def is_google_auth_configured() -> bool:
    """Check if Google OAuth Client ID and Secret are configured."""
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '').strip()
    client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '').strip()
    return bool(client_id) and bool(client_secret)


def get_redirect_uri(request=None) -> str:
    """Build the callback URI for Google OAuth.
    
    In production (DEBUG=False), strictly uses configured GOOGLE_OAUTH_REDIRECT_URI
    or SITE_URL callback, never trusting client-supplied Host headers.
    In development (DEBUG=True), dynamically prioritizes request host for local testing.
    """
    configured_uri = getattr(settings, 'GOOGLE_OAUTH_REDIRECT_URI', '').strip()
    is_debug = getattr(settings, 'DEBUG', True)

    if not is_debug and configured_uri and 'localhost' not in configured_uri and '127.0.0.1' not in configured_uri:
        return configured_uri

    if request is not None and is_debug:
        try:
            dynamic_uri = request.build_absolute_uri(reverse('accounts:google_callback'))
            if not configured_uri or 'localhost' in configured_uri or '127.0.0.1' in configured_uri:
                return dynamic_uri
        except Exception:
            pass

    if configured_uri:
        return configured_uri

    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
    return f"{site_url}/accounts/google/callback/"


def get_google_auth_url(request, next_url: str = None) -> tuple[str, str]:
    """Generate the Google authorization redirect URL and state token.
    
    Returns (auth_url, state).
    """
    state = secrets.token_urlsafe(32)
    redirect_uri = get_redirect_uri(request)
    request.session['google_oauth_state'] = state
    request.session['google_oauth_redirect_uri'] = redirect_uri
    if next_url:
        request.session['google_oauth_next'] = next_url

    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'online',
        'prompt': 'select_account',
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}", state


def verify_id_token_server_side(id_token: str, expected_client_id: str) -> dict:
    """Validate Google OpenID Connect ID token using official google-auth library.
    
    Cryptographically validates:
      - Token signature against Google's public certificates
      - Issuer is accounts.google.com or https://accounts.google.com
      - Audience matches our configured GOOGLE_CLIENT_ID
      - Token is not expired
      - Email is verified
    """
    claims = None
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
        auth_request = google_requests.Request()
        claims = google_id_token.verify_oauth2_token(id_token, auth_request, expected_client_id)
    except ImportError:
        logger.warning("google-auth package not available, falling back to Google tokeninfo endpoint.")
    except Exception as e:
        logger.warning("google.oauth2.id_token verification raised: %s, falling back to tokeninfo endpoint.", e)

    if not claims:
        resp = requests.get(
            GOOGLE_TOKENINFO_URL,
            params={'id_token': id_token},
            timeout=10
        )
        if resp.status_code != 200:
            raise ValueError(f"Google ID token verification failed (HTTP {resp.status_code}): {resp.text}")
        claims = resp.json()

    # 1. Validate audience (aud)
    aud = claims.get('aud')
    if aud != expected_client_id:
        raise ValueError(f"ID token audience mismatch: expected {expected_client_id}, got {aud}")

    # 2. Validate issuer (iss)
    iss = claims.get('iss')
    if iss not in ALLOWED_GOOGLE_ISSUERS:
        raise ValueError(f"Invalid ID token issuer: {iss}")

    # 3. Validate expiration (exp)
    exp = claims.get('exp')
    if not exp:
        raise ValueError("Google ID token is missing required 'exp' claim.")
    try:
        exp_timestamp = float(exp)
    except (ValueError, TypeError):
        raise ValueError("Google ID token has an invalid 'exp' claim format.")

    if exp_timestamp < time.time() - 10:  # 10s leeway for clock skew
        raise ValueError("Google ID token has expired.")

    # 4. Check email verification
    email_verified = claims.get('email_verified')
    if email_verified not in (True, 'true', 'True', 1, '1'):
        raise ValueError("Google account email address is not verified.")

    return claims


def exchange_code_for_user_info(code: str, redirect_uri: str) -> dict:
    """Exchange authorization code for tokens, verify ID token, and return user claims."""
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET

    data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }
    headers = {'Accept': 'application/json'}
    token_resp = requests.post(GOOGLE_TOKEN_URL, data=data, headers=headers, timeout=10)
    if token_resp.status_code != 200:
        logger.error("Google token exchange returned HTTP status %d", token_resp.status_code)
        raise ValueError(f"Failed to exchange authorization code with Google (HTTP {token_resp.status_code}).")

    token_data = token_resp.json()
    id_token = token_data.get('id_token')
    access_token = token_data.get('access_token')

    if not id_token and not access_token:
        raise ValueError("Google token response contained neither id_token nor access_token.")

    user_info = {}
    # Prioritize server-side ID token verification
    if id_token:
        # Strict validation: If ID token verification fails, do NOT silently swallow or downgrade to access_token
        user_info = verify_id_token_server_side(id_token, client_id)
    elif access_token:
        # Fallback only when id_token is not issued (non-OIDC standard response)
        userinfo_resp = requests.get(
            GOOGLE_USERINFO_URL,
            headers={'Authorization': f"Bearer {access_token}"},
            timeout=10
        )
        if userinfo_resp.status_code != 200:
            raise ValueError(f"Failed to fetch userinfo from Google using access token (HTTP {userinfo_resp.status_code}).")
        user_info = userinfo_resp.json()

    if not user_info.get('sub'):
        raise ValueError("Verified Google profile missing unique subject ID (sub).")
    if not user_info.get('email'):
        raise ValueError("Verified Google profile missing email address.")

    return user_info


def get_or_create_google_user(user_info: dict) -> tuple[User, bool]:
    """Find an existing user by Google sub or verified email, or create a new user.
    
    Returns (user, created).
    """
    sub = user_info.get('sub', '').strip()
    email = user_info.get('email', '').strip().lower()
    if not email:
        raise ValueError("Google userinfo did not provide an email address.")

    given_name = user_info.get('given_name', '').strip()
    family_name = user_info.get('family_name', '').strip()
    full_name = user_info.get('name', '').strip()
    if not given_name and full_name:
        parts = full_name.split(' ', 1)
        given_name = parts[0]
        family_name = parts[1] if len(parts) > 1 else ''

    # 1. Primary lookup: Match by immutable Google Subject ID (sub)
    from django.db import transaction
    from accounts.models import UserProfile
    if sub:
        existing_profile = UserProfile.objects.filter(google_sub=sub).select_related('user').first()
        if existing_profile and existing_profile.user:
            user = existing_profile.user
            # Update missing names if empty
            changed = False
            if not user.first_name and given_name:
                user.first_name = given_name
                changed = True
            if not user.last_name and family_name:
                user.last_name = family_name
                changed = True
            if changed:
                user.save(update_fields=['first_name', 'last_name'])
            return user, False

    # 2. Secondary lookup: Match existing user by verified email and link google_sub safely
    user = User.objects.filter(email__iexact=email).first()
    if user:
        if hasattr(user, 'profile'):
            # Security: If account is already linked to a different Google Subject ID, reject!
            if user.profile.google_sub and user.profile.google_sub != sub:
                raise ValueError(
                    f"Account with email '{email}' is already linked to a different Google identity. "
                    "Cannot overwrite existing identity association."
                )
            if sub and user.profile.google_sub != sub:
                user.profile.google_sub = sub
                user.profile.save(update_fields=['google_sub'])
        # Update missing names if empty
        changed = False
        if not user.first_name and given_name:
            user.first_name = given_name
            changed = True
        if not user.last_name and family_name:
            user.last_name = family_name
            changed = True
        if changed:
            user.save(update_fields=['first_name', 'last_name'])
        return user, False

    # 3. New User Provisioning (Atomic transaction to prevent race conditions)
    with transaction.atomic():
        base_username = email.split('@')[0]
        clean_username = re.sub(r'[^a-zA-Z0-9_]', '', base_username) or 'google_user'
        username = clean_username
        counter = 1
        while User.objects.filter(username__iexact=username).exists():
            username = f"{clean_username}_{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=given_name,
            last_name=family_name
        )
        user.set_unusable_password()
        user.save()

        # Configure profile with linked google_sub and enforce strict STUDENT default role
        if hasattr(user, 'profile'):
            profile = user.profile
            if sub:
                profile.google_sub = sub
            if not profile.institution:
                domain = email.split('@')[1] if '@' in email else 'google.com'
                profile.institution = f"{domain.split('.')[0].upper()} Academic"
            profile.role = 'STUDENT'
            profile.save()

        # Ensure ResearcherProfile exists for collaboration & directory
        try:
            from researchers.models import ResearcherProfile
            r_profile, _ = ResearcherProfile.objects.get_or_create(user=user)
            if not r_profile.headline and full_name:
                r_profile.headline = f"Researcher, {user.profile.institution if hasattr(user, 'profile') else 'Institution'}"
                r_profile.save(update_fields=['headline'])
        except Exception as e:
            logger.warning("Could not create/update ResearcherProfile for Google user: %s", e)

        return user, True
