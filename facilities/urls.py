from django.urls import path
from . import views

app_name = 'facilities'

urlpatterns = [
    path('', views.facility_list, name='list'),
    path('<int:pk>/', views.facility_detail, name='detail'),
    path('<int:pk>/book/', views.book_facility, name='book'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('bookings/<int:pk>/decide/', views.decide_booking, name='decide'),
    path('bookings/<int:pk>/cancel/', views.cancel_booking, name='cancel'),
    path('bookings/<int:pk>/log-use/', views.log_use, name='log_use'),
    path('manage/', views.manage_facilities, name='manage'),
    path('utilisation/', views.utilisation_report, name='utilisation'),
]
