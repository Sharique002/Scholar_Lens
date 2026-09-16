from django.urls import path
from . import views

app_name = 'collaboration'

urlpatterns = [
    path('', views.collaboration_list, name='list'),
    path('send/<int:receiver_id>/', views.collaboration_send, name='send'),
    path('<int:pk>/respond/', views.collaboration_respond, name='respond'),
    path('<int:pk>/cancel/', views.collaboration_cancel, name='cancel'),
    path('recommendations/', views.researcher_recommendations, name='recommendations'),
]
