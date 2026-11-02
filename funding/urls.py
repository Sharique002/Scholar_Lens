from django.urls import path
from . import views

app_name = 'funding'

urlpatterns = [
    path('', views.funding_list, name='list'),
    path('<int:pk>/', views.funding_detail, name='detail'),
    path('create/', views.funding_create, name='create'),
    path('<int:pk>/edit/', views.funding_edit, name='edit'),
    path('<int:pk>/watch/', views.funding_watch, name='watch'),
]
