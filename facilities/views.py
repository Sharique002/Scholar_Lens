import csv
from datetime import datetime, time, timedelta, date, timezone as dt_timezone
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
def manage_facilities(request):
    if not (request.user.is_staff or request.user.custodian_facilities.exists()):
        return HttpResponseForbidden("Only custodians and staff can access this page.")

    if request.user.is_staff:
        facilities = Facility.objects.all()
    else:
        facilities = request.user.custodian_facilities.all()

    pending_bookings = Booking.objects.filter(
        facility__in=facilities,
        status='PENDING'
    ).select_related('facility', 'user').order_by('created_at')

    now = timezone.now()
    approved_bookings = Booking.objects.filter(
        facility__in=facilities,
        status='APPROVED'
    ).select_related('facility', 'user').order_by('created_at')
    awaiting_log = [b for b in approved_bookings if b.end and b.end <= now]

    context = {
        'facilities': facilities,
        'pending_bookings': pending_bookings,
        'awaiting_log': awaiting_log,
    }
    return render(request, 'facilities/manage.html', context)


@login_required
def decide_booking(request, pk):
    if request.method != 'POST':
        return HttpResponseForbidden("POST required")

    booking = get_object_or_404(Booking, pk=pk)
    if not booking.facility.can_manage(request.user):
        return HttpResponseForbidden("Not authorized to manage this facility")

    if booking.status != 'PENDING':
        messages.warning(request, "This booking was already decided.")
        return redirect('facilities:manage')

    action = request.POST.get('action')
    if action == 'approve':
        booking.status = 'APPROVED'
        verb = 'approved'
    elif action == 'reject':
        booking.status = 'REJECTED'
        verb = 'rejected'
    else:
        return HttpResponseForbidden("Invalid action")

    booking.decided_by = request.user
    booking.decided_at = timezone.now()
    booking.save(update_fields=['status', 'decided_by', 'decided_at'])

    start_date_str = booking.start.strftime('%Y-%m-%d %H:%M') if booking.start else ''
    ResearchActivity.objects.create(
        user=booking.user,
        activity_type='BOOKING',
        description=f"Your booking for {booking.facility.name} on {start_date_str} was {verb}"
    )

    messages.success(request, f"Booking for {booking.facility.name} was {verb}.")
    return redirect('facilities:manage')


@login_required
def log_use(request, pk):
    if request.method != 'POST':
        return HttpResponseForbidden("POST required")

    booking = get_object_or_404(Booking, pk=pk)
    if not booking.facility.can_manage(request.user):
        return HttpResponseForbidden("Not authorized to manage this facility")

    if booking.status != 'APPROVED':
        messages.error(request, "Only approved bookings can have usage logged.")
        return redirect('facilities:manage')

    if booking.end and booking.end > timezone.now():
        messages.error(request, "Cannot log usage before booking end time.")
        return redirect('facilities:manage')

    outcome = request.POST.get('outcome')
    if outcome == 'completed':
        booking.status = 'COMPLETED'
    elif outcome == 'no_show':
        booking.status = 'NO_SHOW'
    else:
        return HttpResponseForbidden("Invalid outcome")

    booking.save(update_fields=['status'])
    messages.success(request, f"Usage recorded as {booking.get_status_display()}.")
    return redirect('facilities:manage')


@login_required
def utilisation_report(request):
    if not (request.user.is_staff or request.user.custodian_facilities.exists()):
        return HttpResponseForbidden("Only custodians and staff can view utilisation reports.")

    if request.user.is_staff:
        managed_facilities = Facility.objects.filter(is_active=True)
    else:
        managed_facilities = Facility.objects.filter(is_active=True, custodian=request.user)

    week_str = request.GET.get('week', '').strip()
    try:
        if week_str:
            target_date = datetime.strptime(week_str, '%Y-%m-%d').date()
        else:
            today = timezone.localdate()
            this_monday = today - timedelta(days=today.weekday())
            target_date = this_monday - timedelta(days=7)  # default to last full week
    except (ValueError, TypeError):
        today = timezone.localdate()
        this_monday = today - timedelta(days=today.weekday())
        target_date = this_monday - timedelta(days=7)

    week_start = target_date - timedelta(days=target_date.weekday())
    week_end = week_start + timedelta(days=6)
    prev_week = (week_start - timedelta(days=7)).strftime('%Y-%m-%d')
    next_week = (week_start + timedelta(days=7)).strftime('%Y-%m-%d')

    week_start_dt = timezone.make_aware(datetime.combine(week_start, time.min))
    week_end_dt = timezone.make_aware(datetime.combine(week_end, time.max))
    week_range = DateTimeTZRange(week_start_dt, week_end_dt, bounds='[]')

    report_data = []
    for fac in managed_facilities.order_by('name'):
        open_hours = 0.0
        for slot in fac.slots.all():
            open_hours += (datetime.combine(date.today(), slot.closes) - datetime.combine(date.today(), slot.opens)).total_seconds() / 3600.0

        completed = fac.bookings.filter(status='COMPLETED', during__overlap=week_range)
        used_hours = 0.0
        for b in completed:
            if b.start and b.end:
                c_start = max(b.start, week_start_dt)
                c_end = min(b.end, week_end_dt)
                if c_end > c_start:
                    used_hours += (c_end - c_start).total_seconds() / 3600.0

        idle_hours = max(0.0, open_hours - used_hours)
        util_pct = round((used_hours / open_hours * 100)) if open_hours > 0 else 0

        report_data.append({
            'facility': fac,
            'name': fac.name,
            'department': fac.department,
            'open_hours': open_hours,
            'used_hours': used_hours,
            'idle_hours': idle_hours,
            'util_pct': util_pct,
        })

    if request.GET.get('format') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="facilities_utilisation_{week_start}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Facility', 'Department', 'Open Hours', 'Used Hours', 'Idle Hours', 'Utilisation (%)'])
        for r in report_data:
            writer.writerow([r['name'], r['department'], f"{r['open_hours']:.1f}", f"{r['used_hours']:.1f}", f"{r['idle_hours']:.1f}", f"{r['util_pct']}%"])
        return response

    context = {
        'report_data': report_data,
        'week_start': week_start,
        'week_end': week_end,
        'prev_week': prev_week,
        'next_week': next_week,
    }
    return render(request, 'facilities/utilisation.html', context)


def _ics_escape(text):
    # RFC 5545 text escaping
    return str(text).replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')


@login_required
def booking_ics(request, pk):
    """iCalendar export of one approved booking, importable into Google or Outlook calendar."""
    booking = get_object_or_404(Booking.objects.select_related('facility'), pk=pk)
    if booking.user != request.user and not booking.facility.can_manage(request.user):
        return HttpResponseForbidden("Not authorized to export this booking")
    if booking.status != 'APPROVED':
        return HttpResponseForbidden("Only approved bookings can be exported")
    fmt = '%Y%m%dT%H%M%SZ'
    utc = dt_timezone.utc
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Scholar Lens//Facility Booking//EN',
        'BEGIN:VEVENT',
        f'UID:booking-{booking.pk}@scholar-lens',
        f'DTSTAMP:{timezone.now().astimezone(utc).strftime(fmt)}',
        f'DTSTART:{booking.start.astimezone(utc).strftime(fmt)}',
        f'DTEND:{booking.end.astimezone(utc).strftime(fmt)}',
        f'SUMMARY:{_ics_escape(booking.facility.name)}',
        f'LOCATION:{_ics_escape(booking.facility.location)}',
        f'DESCRIPTION:{_ics_escape(booking.purpose)}',
        'END:VEVENT',
        'END:VCALENDAR',
    ]
    response = HttpResponse('\r\n'.join(lines) + '\r\n', content_type='text/calendar; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="booking-{booking.pk}.ics"'
    return response
