from django.urls import path
from . import views

app_name = 'opportunities'

urlpatterns = [
    path('', views.openings_list, name='list'),
    path('create/', views.opening_create, name='create'),
    path('<int:pk>/', views.opening_detail, name='detail'),
    path('<int:pk>/apply/', views.opening_apply, name='apply'),
    path('applications/<int:pk>/<str:action>/', views.application_review, name='review'),
]
