"""scholar_lens URL Configuration."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.http import HttpResponse

urlpatterns = [
    path('favicon.ico', lambda r: HttpResponse(status=204)),
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('researchers/', include('researchers.urls')),
    path('papers/', include('papers.urls')),
    path('projects/', include('projects.urls')),
    path('collaboration/', include('collaboration.urls')),
    path('ai/', include('ai_engine.urls')),
    path('evaluation/', include('evaluation.urls')),
    path('search/', include('search.urls')),
]

# Custom error handlers
handler404 = 'dashboard.views.error_404'
handler403 = 'dashboard.views.error_403'
handler500 = 'dashboard.views.error_500'

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
