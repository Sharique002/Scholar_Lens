from datetime import datetime, time, timedelta, date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError, OperationalError, transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from psycopg2.extras import DateTimeTZRange

from .models import Facility, FacilitySlot, Booking
from .forms import BookingForm
from dashboard.models import ResearchActivity


def create_booking(facility, user, during, purpose, status='PENDING'):
    """
    Creates a Booking inside an atomic transaction.
    The PostgreSQL ExclusionConstraint blocks overlapping active bookings.
    Returns Booking on success, None on IntegrityError or OperationalError (deadlock) conflict.
    """
    try:
        with transaction.atomic():
            booking = Booking.objects.create(
                facility=facility,
                user=user,
                during=during,
                purpose=purpose,
                status=status
            )
            start_str = booking.start.strftime('%Y-%m-%d %H:%M') if booking.start else ''
            ResearchActivity.objects.create(
                user=user,
                activity_type='BOOKING',
                description=f"Requested {facility.name} on {start_str}"
            )
            return booking
    except (IntegrityError, OperationalError):
        return None


@login_required
def facility_list(request):
    qs = Facility.objects.filter(is_active=True)

    q = request.GET.get('q', '').strip()
    kind = request.GET.get('kind', '').strip()
    department = request.GET.get('department', '').strip()

    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(location__icontains=q))
    if kind:
        qs = qs.filter(kind=kind)
    if department:
        qs = qs.filter(department=department)

    departments = Facility.objects.filter(is_active=True).values_list('department', flat=True).distinct().order_by('department')

    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'facilities': page_obj,
        'page_obj': page_obj,
        'q': q,
        'kind': kind,
        'department': department,
        'departments': departments,
        'kinds': Facility.KIND_CHOICES,
    }
    return render(request, 'facilities/list.html', context)


@login_required
def facility_detail(request, pk):
    facility = get_object_or_404(Facility, pk=pk)

    week_str = request.GET.get('week', '').strip()
    try:
        if week_str:
            target_date = datetime.strptime(week_str, '%Y-%m-%d').date()
        else:
            target_date = timezone.localdate()
    except (ValueError, TypeError):
        target_date = timezone.localdate()

    # Align to Monday of that week
    week_start = target_date - timedelta(days=target_date.weekday())
    prev_week = (week_start - timedelta(days=7)).strftime('%Y-%m-%d')
    next_week = (week_start + timedelta(days=7)).strftime('%Y-%m-%d')

    slots = list(facility.slots.all().order_by('opens'))
    days = []
    for i in range(7):
        day_date = week_start + timedelta(days=i)
        day_weekday = day_date.weekday()
        day_slots = [s for s in slots if s.weekday == day_weekday]

        day_start = timezone.make_aware(datetime.combine(day_date, time.min))
        day_end = timezone.make_aware(datetime.combine(day_date, time.max))
        day_range = DateTimeTZRange(day_start, day_end, bounds='[]')

        day_bookings = facility.bookings.filter(
            status__in=['PENDING', 'APPROVED'],
            during__overlap=day_range
        ).order_by('during')

        days.append({
            'date': day_date,
            'weekday_name': day_date.strftime('%A'),
            'slots': day_slots,
            'bookings': day_bookings,
        })

    context = {
        'facility': facility,
        'week_start': week_start,
        'days': days,
        'prev_week': prev_week,
        'next_week': next_week,
        'can_manage': facility.can_manage(request.user),
    }
    return render(request, 'facilities/detail.html', context)


@login_required
def book_facility(request, pk):
    facility = get_object_or_404(Facility, pk=pk, is_active=True)

    if request.method == 'POST':
        form = BookingForm(request.POST, facility=facility)
        if form.is_valid():
            status = 'APPROVED' if not facility.requires_approval else 'PENDING'
            booking = create_booking(
                facility=facility,
                user=request.user,
                during=form.cleaned_data['during'],
                purpose=form.cleaned_data['purpose'],
                status=status
            )
            if booking:
                if facility.requires_approval:
                    messages.success(request, "Booking requested. The custodian will approve it soon.")
                else:
                    messages.success(request, "Booking confirmed.")
                return redirect('facilities:my_bookings')
            else:
                form.add_error(None, "That time was just taken. Please pick another slot.")
                return render(request, 'facilities/book.html', {'facility': facility, 'form': form}, status=200)
    else:
        initial_date = request.GET.get('date', timezone.localdate().strftime('%Y-%m-%d'))
        form = BookingForm(facility=facility, initial={'date': initial_date})

    return render(request, 'facilities/book.html', {'facility': facility, 'form': form})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('facility').order_by('-created_at')
    return render(request, 'facilities/my_bookings.html', {
        'bookings': bookings,
        'now': timezone.now(),
    })


@login_required
def decide_booking(request, pk):
    return redirect('facilities:manage')


@login_required
def cancel_booking(request, pk):
    if request.method != 'POST':
        return HttpResponseForbidden("POST required")
    booking = get_object_or_404(Booking, pk=pk)
    if booking.user != request.user and not (request.user.is_staff or booking.facility.can_manage(request.user)):
        return HttpResponseForbidden("Not authorized to cancel this booking")

    booking.status = 'CANCELLED'
    booking.save(update_fields=['status'])
    messages.success(request, "Booking cancelled.")
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
