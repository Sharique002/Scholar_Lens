"""scholar_lens URL Configuration."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.http import HttpResponse
from django.urls import re_path
from django.views.static import serve

urlpatterns = [
    path('favicon.ico', lambda r: HttpResponse(status=204)),
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('researchers/', include('researchers.urls')),
    path('papers/', include('papers.urls')),
    path('projects/', include('projects.urls')),
    path('collaboration/', include('collaboration.urls')),
    path('facilities/', include('facilities.urls')),
    path('funding/', include('funding.urls')),
    path('opportunities/', include('opportunities.urls')),
    path('analytics/', include('analytics.urls')),
    path('ai/', include('ai_engine.urls')),
    path('evaluation/', include('evaluation.urls')),
    path('search/', include('search.urls')),
]

# Custom error handlers
handler404 = 'dashboard.views.error_404'
handler403 = 'dashboard.views.error_403'
handler500 = 'dashboard.views.error_500'

# Serve media files across environments
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

# Serve static files in development (WhiteNoise handles static in production)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
