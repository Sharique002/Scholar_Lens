"""WSGI config for scholar_lens project."""
import os
import sys
from pathlib import Path

# Add project root to sys.path for serverless container resolution
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scholar_lens.settings')

import django
django.setup()

def ensure_database_ready():
    """Verify that required database tables exist; migrate and initialize admin if not."""
    try:
        from django.db import connection
        from django.core.management import call_command
        tables = connection.introspection.table_names()
        if 'auth_user' not in tables:
            print("[Vercel Init] Required tables missing. Running migrate...")
            call_command('migrate', interactive=False, verbosity=0)
            print("[Vercel Init] Migrations applied.")
            try:
                call_command('init_admin', verbosity=0)
                print("[Vercel Init] Default admin initialized.")
            except Exception as e:
                print(f"[Vercel Init] init_admin notice: {e}")
    except Exception as exc:
        print(f"[Vercel Init] Database readiness check notice: {exc}")

# Run check on startup
is_serverless = bool(
    os.environ.get('VERCEL')
    or os.environ.get('VERCEL_ENV')
    or os.environ.get('VERCEL_REGION')
    or os.environ.get('NOW_REGION')
    or os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
    or not os.access(str(BASE_DIR), os.W_OK)
)
if is_serverless:
    ensure_database_ready()

from django.core.wsgi import get_wsgi_application

django_app = get_wsgi_application()

_db_checked = False

def app(environ, start_response):
    """WSGI callable for Vercel Serverless Function with exception traceback logging."""
    global _db_checked
    if not _db_checked and is_serverless:
        ensure_database_ready()
        _db_checked = True

    try:
        return django_app(environ, start_response)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise exc


application = app


