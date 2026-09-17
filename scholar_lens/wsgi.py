"""WSGI config for scholar_lens project."""
import os
import sys
from pathlib import Path

# Add project root to sys.path for serverless container resolution
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scholar_lens.settings')

# Auto-migrate SQLite if running on Vercel/serverless with a fresh /tmp database
if os.environ.get('VERCEL') or os.environ.get('NOW_REGION'):
    try:
        import django
        django.setup()
        from django.conf import settings
        from django.core.management import call_command
        db_conf = settings.DATABASES.get('default', {})
        if db_conf.get('ENGINE') == 'django.db.backends.sqlite3':
            db_file = Path(db_conf.get('NAME', ''))
            # Check if sqlite db is new or unmigrated in /tmp
            if str(db_file).startswith('/tmp') and (not db_file.exists() or db_file.stat().st_size == 0):
                call_command('migrate', interactive=False, verbosity=0)
                try:
                    call_command('init_admin', verbosity=0)
                except Exception:
                    pass
    except Exception as e:
        print(f"[Vercel Init] Database bootstrap note: {e}")

from django.core.wsgi import get_wsgi_application

django_app = get_wsgi_application()


def app(environ, start_response):
    """WSGI callable for Vercel Serverless Function with exception traceback logging."""
    try:
        return django_app(environ, start_response)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise exc


application = app

