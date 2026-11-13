"""
Django settings for scholar_lens project.
"""
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Try to load .env file
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass

# Helper to safely parse integer environment variables with empty string safety
def get_int_env(key, default):
    val = os.environ.get(key, None)
    if val is None or str(val).strip() == '':
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

# Helper to safely parse string environment variables with empty string safety
def get_str_env(key, default):
    val = os.environ.get(key, None)
    if val is None or str(val).strip() == '':
        return default
    return str(val).strip()

def get_bool_env(key, default=False):
    val = os.environ.get(key, None)
    if val is None or str(val).strip() == '':
        return default
    return str(val).strip().lower() in ('true', '1', 'yes')

E2E = get_bool_env('E2E', False)

# Environment & Debug Configuration
raw_debug = os.environ.get('DEBUG', None)
if raw_debug is not None:
    DEBUG = raw_debug.strip().lower() in ('true', '1', 'yes')
elif os.environ.get('RENDER') or os.environ.get('RENDER_EXTERNAL_HOSTNAME') or os.environ.get('ENVIRONMENT') == 'production':
    DEBUG = False
else:
    DEBUG = True

# Security: SECRET_KEY
SECRET_KEY = get_str_env('SECRET_KEY', None)
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-dev-key-change-this-in-production-abc123xyz'
    else:
        raise ImproperlyConfigured("SECRET_KEY must be configured via environment variable in production (DEBUG=False).")

if not DEBUG:
    if SECRET_KEY.startswith('django-insecure') or len(SECRET_KEY) < 32:
        raise ImproperlyConfigured("Production SECRET_KEY must be a cryptographically secure key of at least 32 characters.")


# Allowed Hosts Configuration
raw_hosts = os.environ.get('ALLOWED_HOSTS', '')
if raw_hosts:
    clean_hosts = []
    for h in raw_hosts.split(','):
        h = h.strip()
        if not h:
            continue
        if h.startswith('*.'):
            clean_hosts.append('.' + h[2:])
        else:
            clean_hosts.append(h)
    ALLOWED_HOSTS = clean_hosts
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1'] if DEBUG else []

render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if render_host and render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_host)

vercel_host = os.environ.get('VERCEL_URL')
if vercel_host and vercel_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(vercel_host)

if not DEBUG:
    if '*' in ALLOWED_HOSTS:
        raise ImproperlyConfigured("Wildcard '*' in ALLOWED_HOSTS is strictly forbidden in production (DEBUG=False).")
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured("ALLOWED_HOSTS must be explicitly defined when DEBUG=False.")
else:
    for default_host in ['localhost', '127.0.0.1', '.onrender.com', 'scholar-lens.onrender.com']:
        if default_host not in ALLOWED_HOSTS and '*' not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(default_host)

# CSRF Trusted Origins Configuration
raw_csrf = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if raw_csrf:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in raw_csrf.split(',') if origin.strip()]
else:
    CSRF_TRUSTED_ORIGINS = []

if DEBUG:
    for origin in ['http://localhost:8000', 'http://127.0.0.1:8000', 'http://localhost:8001', 'http://127.0.0.1:8001']:
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)

if render_host:
    rendered_origin = render_host if render_host.startswith(('http://', 'https://')) else f"https://{render_host}"
    if rendered_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(rendered_origin)

if vercel_host:
    v_origin = vercel_host if vercel_host.startswith(('http://', 'https://')) else f"https://{vercel_host}"
    if v_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(v_origin)

# SSL Proxy Header (standard for Render, Railway, Fly.io, Heroku, Nginx, Vercel)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Scholar Lens apps
    'accounts.apps.AccountsConfig',
    'researchers.apps.ResearchersConfig',
    'papers.apps.PapersConfig',
    'projects.apps.ProjectsConfig',
    'collaboration.apps.CollaborationConfig',
    'ai_engine.apps.AiEngineConfig',
    'evaluation.apps.EvaluationConfig',
    'search.apps.SearchConfig',
    'dashboard.apps.DashboardConfig',
    'django.contrib.postgres',
    'facilities.apps.FacilitiesConfig',
    'funding.apps.FundingConfig',
    'opportunities.apps.OpportunitiesConfig',
    'analytics.apps.AnalyticsConfig',
]

MIDDLEWARE = [
    'scholar_lens.middleware.ExceptionCaptureMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'scholar_lens.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'scholar_lens.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'scholar_lens.wsgi.application'

# Serverless / Cloud detection (Vercel, AWS Lambda)
IS_SERVERLESS = bool(
    os.environ.get('VERCEL')
    or os.environ.get('VERCEL_ENV')
    or os.environ.get('VERCEL_REGION')
    or os.environ.get('NOW_REGION')
    or os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
)

# Database
import dj_database_url

DATABASE_URL = get_str_env('DATABASE_URL', None)
USE_POSTGRES = os.environ.get('USE_POSTGRES', 'False').lower() in ('true', '1', 'yes')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
elif USE_POSTGRES:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'scholar_lens'),
            'USER': os.environ.get('DB_USER', 'scholar_lens'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'scholar_lens'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    if not DEBUG:
        raise ImproperlyConfigured("SQLite fallback is strictly forbidden in production (DEBUG=False). Please configure a PostgreSQL DATABASE_URL.")
    # On Vercel serverless, root filesystem is read-only; use /tmp
    db_file = Path('/tmp/db.sqlite3') if IS_SERVERLESS else (BASE_DIR / 'db.sqlite3')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': db_file,
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
# In serverless environments, allow WhiteNoise to serve directly from finders if collectstatic wasn't run
WHITENOISE_USE_FINDERS = True

# Persistent Storage (Cloudflare R2 / S3-compatible backend)
USE_R2_STORAGE = get_bool_env('USE_R2_STORAGE', False) or get_bool_env('USE_S3_STORAGE', False)

if USE_R2_STORAGE:
    if 'storages' not in INSTALLED_APPS:
        INSTALLED_APPS.append('storages')

    AWS_ACCESS_KEY_ID = os.environ.get('R2_ACCESS_KEY_ID') or os.environ.get('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.environ.get('R2_SECRET_ACCESS_KEY') or os.environ.get('AWS_SECRET_ACCESS_KEY', '')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('R2_BUCKET_NAME') or os.environ.get('AWS_STORAGE_BUCKET_NAME', '')
    AWS_S3_ENDPOINT_URL = os.environ.get('R2_ENDPOINT_URL') or os.environ.get('AWS_S3_ENDPOINT_URL', '')
    AWS_S3_REGION_NAME = os.environ.get('R2_REGION_NAME', 'auto')
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = get_bool_env('AWS_QUERYSTRING_AUTH', True)
    AWS_QUERYSTRING_EXPIRE = get_int_env('AWS_QUERYSTRING_EXPIRE', 3600)
    AWS_S3_FILE_OVERWRITE = False
    AWS_LOCATION = os.environ.get('R2_MEDIA_LOCATION', 'media')

    r2_custom_domain = os.environ.get('R2_CUSTOM_DOMAIN') or os.environ.get('AWS_S3_CUSTOM_DOMAIN', '')
    if r2_custom_domain:
        AWS_S3_CUSTOM_DOMAIN = r2_custom_domain
        MEDIA_URL = f"https://{r2_custom_domain}/{AWS_LOCATION}/"
    elif AWS_S3_ENDPOINT_URL and AWS_STORAGE_BUCKET_NAME:
        MEDIA_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/{AWS_LOCATION}/"
    else:
        MEDIA_URL = '/media/'

    MEDIA_ROOT = Path('/tmp/media') if IS_SERVERLESS else (BASE_DIR / 'media')
    STORAGES = {
        "default": {
            "BACKEND": "scholar_lens.storage.R2MediaStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }
    DEFAULT_FILE_STORAGE = 'scholar_lens.storage.R2MediaStorage'
else:
    # Media files (Local filesystem fallback for local development and offline tests)
    MEDIA_URL = '/media/'
    MEDIA_ROOT = Path('/tmp/media') if IS_SERVERLESS else (BASE_DIR / 'media')
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Session settings
SESSION_ENGINE = os.environ.get(
    'SESSION_ENGINE',
    'django.contrib.sessions.backends.signed_cookies' if (IS_SERVERLESS and not DATABASE_URL) else 'django.contrib.sessions.backends.db'
)
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# CSRF
CSRF_COOKIE_HTTPONLY = False  # Allow JS access if needed
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = 'Lax'

# Production SSL & Security Headers
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_SSL_REDIRECT = get_bool_env('SECURE_SSL_REDIRECT', True)
    if SECURE_SSL_REDIRECT:
        SECURE_HSTS_SECONDS = get_int_env('SECURE_HSTS_SECONDS', 31536000)
        SECURE_HSTS_INCLUDE_SUBDOMAINS = get_bool_env('SECURE_HSTS_INCLUDE_SUBDOMAINS', True)
        SECURE_HSTS_PRELOAD = get_bool_env('SECURE_HSTS_PRELOAD', False)

# File upload settings
MAX_UPLOAD_SIZE_MB = get_int_env('MAX_UPLOAD_SIZE_MB', 20)
MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024  # Convert to bytes
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE

# AI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OPENAI_MODEL = get_str_env('OPENAI_MODEL', 'gpt-4o-mini')
OPENAI_EMBEDDING_MODEL = get_str_env('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')

# Google Scholar Configuration
SERPAPI_API_KEY = os.environ.get('SERPAPI_API_KEY', '')
SCOPUS_API_KEY = os.environ.get('SCOPUS_API_KEY', '')  # Elsevier licence key for Scopus import
SCHOLAR_API_PROVIDER = get_str_env('SCHOLAR_API_PROVIDER', 'serpapi')
SCHOLAR_API_TIMEOUT = get_int_env('SCHOLAR_API_TIMEOUT', 10)
SCHOLAR_MAX_RESULTS = get_int_env('SCHOLAR_MAX_RESULTS', 5)

# Site configuration
SITE_NAME = get_str_env('SITE_NAME', 'Scholar Lens')
SITE_URL = get_str_env('SITE_URL', 'http://localhost:8000')

# Google OAuth2 Single Sign-On (SSO)
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_OAUTH_REDIRECT_URI = os.environ.get(
    'GOOGLE_OAUTH_REDIRECT_URI',
    f"{SITE_URL.rstrip('/')}/accounts/google/callback/"
)

# Canonical Scholar Lens Evaluation Framework Weights (must sum to 100)
EVALUATION_WEIGHTS = {
    'novelty': 20,              # Potential Novelty (20%)
    'research_gap': 15,         # Research Gap (15%)
    'methodology': 15,          # Methodology (15%)
    'contribution': 15,         # Contribution (15%)
    'evidence_quality': 15,     # Evidence Quality (15%)
    'technical_strength': 10,   # Technical Strength (10%)
    'clarity': 10,              # Clarity (10%)
}

# Logging configuration
# On serverless (e.g. Vercel) filesystem is read-only; stream to console for Vercel Function Logs
LOG_HANDLERS = ['console']
HANDLERS_CONFIG = {
    'console': {
        'class': 'logging.StreamHandler',
        'formatter': 'verbose',
    },
}

# Only attach file handler if local, in DEBUG, and directory is writable
if not IS_SERVERLESS and DEBUG:
    try:
        log_file = BASE_DIR / 'debug.log'
        with open(log_file, 'a'):
            pass
        HANDLERS_CONFIG['file'] = {
            'class': 'logging.FileHandler',
            'filename': log_file,
            'formatter': 'verbose',
        }
        LOG_HANDLERS.append('file')
    except (OSError, IOError, PermissionError):
        pass

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': HANDLERS_CONFIG,
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'scholar_lens': {
            'handlers': LOG_HANDLERS,
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
    },
}



# P08 Module Configuration
FUNDING_ALERT_DAYS = [int(x) for x in os.environ.get('FUNDING_ALERT_DAYS', '30,14,7,1').split(',') if x.strip()]
MILESTONE_AT_RISK_DAYS = int(os.environ.get('MILESTONE_AT_RISK_DAYS', 7))
MILESTONE_AT_RISK_PROGRESS = int(os.environ.get('MILESTONE_AT_RISK_PROGRESS', 50))
