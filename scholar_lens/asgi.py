"""ASGI config for scholar_lens project."""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scholar_lens.settings')
application = get_asgi_application()
