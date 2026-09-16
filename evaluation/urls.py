from django.urls import path
from . import views

app_name = 'evaluation'

urlpatterns = [
    path('<int:paper_id>/', views.evaluate_paper, name='evaluate'),
    path('report/<int:report_id>/', views.evaluation_report, name='report'),
    path('<int:paper_id>/similarity/', views.similarity_analysis, name='similarity'),
]
