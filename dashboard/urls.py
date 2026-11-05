from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('dashboard/', views.dashboard_view, name='home'),
    path('dashboard/office/', views.office_hub, name='office'),
    path('dashboard/notifications/', views.notifications_view, name='notifications'),
    path('dashboard/settings/', views.settings_view, name='settings'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('terms/', views.terms_of_service, name='terms'),
]
