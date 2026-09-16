from django.urls import path
from . import views

app_name = 'papers'

urlpatterns = [
    path('', views.paper_list, name='list'),
    path('upload/', views.paper_upload, name='upload'),
    path('<int:pk>/', views.paper_detail, name='detail'),
    path('<int:pk>/edit/', views.paper_edit, name='edit'),
    path('<int:pk>/delete/', views.paper_delete, name='delete'),
    path('<int:pk>/download/', views.paper_download, name='download'),
]
