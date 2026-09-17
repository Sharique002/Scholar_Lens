"""
Django settings for scholar_lens project.
"""
import os
from pathlib import Path

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

# Security
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-dev-key-change-this-in-production-abc123xyz'
)
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

# Allowed Hosts
raw_hosts = os.environ.get('ALLOWED_HOSTS', '*,localhost,127.0.0.1,.onrender.com,.vercel.app').split(',')
ALLOWED_HOSTS = [h.strip() for h in raw_hosts if h.strip()]
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['*']

render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if render_host and render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_host)

vercel_host = os.environ.get('VERCEL_URL')
if vercel_host and vercel_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(vercel_host)

if '.onrender.com' not in ALLOWED_HOSTS and '*' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('.onrender.com')
if 'scholar-lens.onrender.com' not in ALLOWED_HOSTS and '*' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('scholar-lens.onrender.com')
if '.vercel.app' not in ALLOWED_HOSTS and '*' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('.vercel.app')

# CSRF Trusted Origins (required for HTTPS in Django 4+)
raw_csrf = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if raw_csrf:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in raw_csrf.split(',') if origin.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        'https://*.onrender.com',
        'https://scholar-lens.onrender.com',
        'https://*.vercel.app',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]

if 'https://*.onrender.com' not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append('https://*.onrender.com')
if 'https://scholar-lens.onrender.com' not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append('https://scholar-lens.onrender.com')
if 'https://*.vercel.app' not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append('https://*.vercel.app')
if render_host:
    rendered_origin = f"https://{render_host}"
    if rendered_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(rendered_origin)
if vercel_host:
    v_origin = f"https://{vercel_host}"
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
    or not os.access(str(BASE_DIR), os.W_OK)
)

# Database
import dj_database_url

DATABASE_URL = os.environ.get('DATABASE_URL')
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

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = Path('/tmp/media') if IS_SERVERLESS else (BASE_DIR / 'media')

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
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# CSRF
CSRF_COOKIE_HTTPONLY = False  # Allow JS access if needed
CSRF_COOKIE_SECURE = not DEBUG

# Production SSL & Security Headers
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1', 'yes')
    if SECURE_SSL_REDIRECT:
        SECURE_HSTS_SECONDS = get_int_env('SECURE_HSTS_SECONDS', 31536000)
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True
        SECURE_HSTS_PRELOAD = True

# File upload settings
MAX_UPLOAD_SIZE_MB = get_int_env('MAX_UPLOAD_SIZE_MB', 20)
MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024  # Convert to bytes
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE

# AI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
OPENAI_EMBEDDING_MODEL = os.environ.get('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')

# Google Scholar Configuration
SERPAPI_API_KEY = os.environ.get('SERPAPI_API_KEY', '')
SCHOLAR_API_PROVIDER = os.environ.get('SCHOLAR_API_PROVIDER', 'serpapi')
SCHOLAR_API_TIMEOUT = get_int_env('SCHOLAR_API_TIMEOUT', 10)
SCHOLAR_MAX_RESULTS = get_int_env('SCHOLAR_MAX_RESULTS', 5)

# Site configuration
SITE_NAME = os.environ.get('SITE_NAME', 'Scholar Lens')
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')

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

