from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search_view, name='search'),
    path('expertise/', views.expertise_search, name='expertise'),
]
