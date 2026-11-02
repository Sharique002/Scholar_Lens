from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from .models import Facility, Booking


def facility_list(request):
    facilities = Facility.objects.filter(is_active=True)
    return render(request, 'facilities/list.html', {'facilities': facilities})


def facility_detail(request, pk):
    facility = get_object_or_404(Facility, pk=pk)
    return render(request, 'facilities/detail.html', {'facility': facility})


@login_required
def book_facility(request, pk):
    facility = get_object_or_404(Facility, pk=pk)
    return render(request, 'facilities/book.html', {'facility': facility})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user)
    return render(request, 'facilities/my_bookings.html', {'bookings': bookings})


@login_required
def decide_booking(request, pk):
    return redirect('facilities:manage')


@login_required
def cancel_booking(request, pk):
    return redirect('facilities:my_bookings')


@login_required
def log_use(request, pk):
    return redirect('facilities:manage')


@login_required
def manage_facilities(request):
    return render(request, 'facilities/manage.html', {})


@login_required
def utilisation_report(request):
    return render(request, 'facilities/utilisation.html', {})
