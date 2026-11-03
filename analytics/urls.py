from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.research_report, name='research'),
    path('research/', views.research_report, name='research_sub'),
    path('report/', views.research_report, name='report'),
]
