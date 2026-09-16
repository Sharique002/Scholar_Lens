from django.urls import path
from . import views

app_name = 'ai_engine'

urlpatterns = [
    path('<int:paper_id>/summary/', views.paper_summary, name='summary'),
    path('<int:paper_id>/gaps/', views.paper_gaps, name='gaps'),
    path('<int:paper_id>/ask/', views.ask_paper, name='ask_paper'),
    path('<int:paper_id>/process/', views.process_paper_view, name='process_paper'),
]
