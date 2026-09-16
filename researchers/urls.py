from django.urls import path
from . import views

app_name = 'researchers'

urlpatterns = [
    path('', views.researcher_list, name='list'),
    path('<int:pk>/', views.researcher_detail, name='detail'),
    path('profile/edit/', views.researcher_profile_edit, name='edit_profile'),
    path('interests/add/', views.researcher_add_interest, name='add_interest'),
    path('interests/<int:pk>/remove/', views.researcher_remove_interest, name='remove_interest'),
    path('skills/add/', views.researcher_add_skill, name='add_skill'),
]
