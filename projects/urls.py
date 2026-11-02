from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='list'),
    path('create/', views.project_create, name='create'),
    path('at-risk/', views.at_risk_board, name='at_risk'),
    path('<int:pk>/', views.project_detail, name='detail'),
    path('<int:pk>/edit/', views.project_edit, name='edit'),
    path('<int:pk>/delete/', views.project_delete, name='delete'),
    path('<int:pk>/add-member/', views.project_add_member, name='add_member'),
    path('<int:pk>/leave/', views.project_leave, name='leave'),
    path('<int:pk>/milestones/', views.project_milestones, name='milestones'),
    path('<int:pk>/milestones/create/', views.milestone_create, name='milestone_create'),
    path('milestones/<int:pk>/edit/', views.milestone_edit, name='milestone_edit'),
    path('milestones/<int:pk>/delete/', views.milestone_delete, name='milestone_delete'),
    path('milestones/<int:pk>/progress/', views.milestone_progress, name='milestone_progress'),
]
