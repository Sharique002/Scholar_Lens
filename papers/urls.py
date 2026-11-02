from django.urls import path
from . import views

app_name = 'papers'

urlpatterns = [
    path('', views.paper_list, name='list'),
    path('upload/', views.paper_upload, name='upload'),
    path('import/', views.import_publications_view, name='import_publications'),
    path('dedup/queue/', views.dedup_queue, name='dedup_queue'),
    path('dedup/<int:candidate_id>/decide/', views.dedup_decide, name='dedup_decide'),
    path('authors/queue/', views.author_queue, name='author_queue'),
    path('authors/<int:author_id>/decide/', views.author_decide, name='author_decide'),
    path('<int:pk>/', views.paper_detail, name='detail'),
    path('<int:pk>/edit/', views.paper_edit, name='edit'),
    path('<int:pk>/delete/', views.paper_delete, name='delete'),
    path('<int:pk>/download/', views.paper_download, name='download'),
    path('<int:paper_id>/unmerge/', views.unmerge_paper, name='unmerge'),
]
