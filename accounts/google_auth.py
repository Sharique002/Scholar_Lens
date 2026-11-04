"""Google OAuth2 Authentication Service for Scholar Lens."""
import logging
import secrets
import urllib.parse
import re
import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def is_google_auth_configured() -> bool:
    """Check if Google OAuth Client ID and Secret are configured."""
    return bool(getattr(settings, 'GOOGLE_CLIENT_ID', '').strip()) and bool(getattr(settings, 'GOOGLE_CLIENT_SECRET', '').strip())


def get_redirect_uri(request) -> str:
    """Build the absolute callback URI for Google OAuth."""
    configured_uri = getattr(settings, 'GOOGLE_OAUTH_REDIRECT_URI', '').strip()
    if configured_uri:
        return configured_uri
    return request.build_absolute_uri(reverse('accounts:google_callback'))


def get_google_auth_url(request, next_url: str = None) -> tuple[str, str]:
    """Generate the Google authorization redirect URL and state token.
    
    Returns (auth_url, state).
    """
    state = secrets.token_urlsafe(32)
    request.session['google_oauth_state'] = state
    if next_url:
        request.session['google_oauth_next'] = next_url

    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': get_redirect_uri(request),
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'online',
        'prompt': 'select_account',
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}", state


def exchange_code_for_user_info(code: str, redirect_uri: str) -> dict:
    """Exchange authorization code for access token and fetch Google profile."""
    data = {
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }
    headers = {'Accept': 'application/json'}
    token_resp = requests.post(GOOGLE_TOKEN_URL, data=data, headers=headers, timeout=10)
    token_resp.raise_for_status()
    token_data = token_resp.json()
    access_token = token_data.get('access_token')
    if not access_token:
        raise ValueError("Google token response did not contain access_token.")

    userinfo_resp = requests.get(
        GOOGLE_USERINFO_URL,
        headers={'Authorization': f"Bearer {access_token}"},
        timeout=10
    )
    userinfo_resp.raise_for_status()
    return userinfo_resp.json()


def get_or_create_google_user(user_info: dict) -> tuple[User, bool]:
    """Find an existing user by email or create a new user from Google profile data.
    
    Returns (user, created).
    """
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

    user = User.objects.filter(email__iexact=email).first()
    if user:
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
        created = False
    else:
        # Generate clean, unique username
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
        created = True

    # Ensure UserProfile exists with institutional details
    if hasattr(user, 'profile'):
        profile = user.profile
        if not profile.institution:
            domain = email.split('@')[1] if '@' in email else 'google.com'
            profile.institution = f"{domain.split('.')[0].upper()} Academic"
        if created:
            # Set default role
            profile.role = 'STUDENT'
        profile.save()

    # Ensure ResearcherProfile exists for topic matching & directory
    try:
        from researchers.models import ResearcherProfile
        r_profile, _ = ResearcherProfile.objects.get_or_create(user=user)
        if not r_profile.headline and full_name:
            r_profile.headline = f"Researcher, {user.profile.institution if hasattr(user, 'profile') else 'Institution'}"
            r_profile.save(update_fields=['headline'])
    except Exception as e:
        logger.warning("Could not create/update ResearcherProfile for Google user: %s", e)

    return user, created
