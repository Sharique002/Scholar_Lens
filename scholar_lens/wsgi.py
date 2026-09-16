"""WSGI config for scholar_lens project."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scholar_lens.settings')
application = get_wsgi_application()
