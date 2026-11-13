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

import shutil
from django.core.wsgi import get_wsgi_application

django_app = get_wsgi_application()

is_serverless = bool(
    os.environ.get('VERCEL')
    or os.environ.get('VERCEL_ENV')
    or os.environ.get('VERCEL_REGION')
    or os.environ.get('NOW_REGION')
    or os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
    or not os.access(str(BASE_DIR), os.W_OK)
)

_db_ready = False

def ensure_database_ready():
    """Verify that required database tables exist; migrate and initialize admin if not."""
    global _db_ready
    if _db_ready:
        return
    _db_ready = True

    try:
        from django.conf import settings
        db_conf = settings.DATABASES.get('default', {})
        db_path = db_conf.get('NAME')

        # If running on serverless SQLite and /tmp/db.sqlite3 doesn't exist yet, seed from repo if available
        if db_path and str(db_path).startswith('/tmp'):
            tmp_db = Path(db_path)
            base_db = BASE_DIR / 'db.sqlite3'
            if not tmp_db.exists() and base_db.exists():
                try:
                    shutil.copy2(base_db, tmp_db)
                    print(f"[Serverless Init] Seeded database from {base_db} to {tmp_db}")
                except Exception as ce:
                    print(f"[Serverless Init] Could not seed database: {ce}")

        from django.db import connection
        from django.core.management import call_command
        tables = connection.introspection.table_names()
        if 'auth_user' not in tables:
            print("[Serverless Init] Required tables missing. Running migrate...")
            call_command('migrate', interactive=False, verbosity=0)
            print("[Serverless Init] Migrations applied.")
            try:
                call_command('init_admin', verbosity=0)
                print("[Serverless Init] Default accounts initialized.")
            except Exception as e:
                print(f"[Serverless Init] init_admin notice: {e}")
    except Exception as exc:
        print(f"[Serverless Init] Database readiness check notice: {exc}")


def app(environ, start_response):
    """WSGI callable for Vercel/serverless environments with exception traceback logging."""
    if is_serverless:
        ensure_database_ready()

    # Ensure HTTPS scheme is propagated properly behind reverse proxies
    if 'HTTP_X_FORWARDED_PROTO' not in environ and environ.get('wsgi.url_scheme') == 'https':
        environ['HTTP_X_FORWARDED_PROTO'] = 'https'

    try:
        return django_app(environ, start_response)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        try:
            status = '500 Internal Server Error'
            headers = [('Content-Type', 'text/html; charset=utf-8')]
            start_response(status, headers)
            body = (
                "<!DOCTYPE html><html><head><title>Scholar Lens Error</title></head>"
                "<body style='font-family:sans-serif;padding:2rem;max-width:800px;margin:auto;'>"
                "<h2>Scholar Lens Server Notice</h2>"
                f"<p>An unexpected exception occurred: <code>{exc}</code></p>"
                "</body></html>"
            )
            return [body.encode('utf-8')]
        except Exception:
            raise exc


application = app
handler = app



