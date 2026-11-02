from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone

from .models import FundingCall
from .forms import FundingCallForm
from projects.models import ResearchProject


@login_required
def funding_list(request):
    if request.user.is_staff:
        calls = FundingCall.objects.all()
    else:
        calls = FundingCall.objects.filter(is_published=True)

    area = request.GET.get('area', '').strip()
    if area:
        calls = calls.filter(research_area=area)

    q = request.GET.get('q', '').strip()
    if q:
        calls = calls.filter(Q(title__icontains=q) | Q(sponsor__icontains=q) | Q(description__icontains=q))

    state = request.GET.get('state', '').strip().lower()
    now = timezone.now()
    today = timezone.localdate()

    open_calls = []
    closed_calls = []

    for call in calls:
        days = call.days_left(today)
        if days < 0:
            closed_calls.append(call)
        else:
            open_calls.append(call)

    if state == 'closing':
        open_calls = [c for c in open_calls if c.days_left(today) <= 14]
        closed_calls = []
    elif state == 'open':
        closed_calls = []
    elif state == 'closed':
        open_calls = []

    watched_call_ids = set(request.user.watched_funding_calls.values_list('id', flat=True))

    context = {
        'open_calls': open_calls,
        'closed_calls': closed_calls,
        'selected_area': area,
        'selected_state': state,
        'q': q,
        'research_areas': ResearchProject.RESEARCH_AREA_CHOICES,
        'watched_call_ids': watched_call_ids,
    }
    return render(request, 'funding/list.html', context)


@login_required
def funding_detail(request, pk):
    call = get_object_or_404(FundingCall, pk=pk)
    if not call.is_published and not request.user.is_staff:
        raise PermissionDenied("This funding call is unpublished.")

    is_watched = call.watchers.filter(pk=request.user.pk).exists()
    return render(request, 'funding/detail.html', {
        'call': call,
        'is_watched': is_watched,
    })


@login_required
def funding_create(request):
    if not request.user.is_staff:
        raise PermissionDenied("Only Research Office staff can create funding calls.")

    if request.method == 'POST':
        form = FundingCallForm(request.POST)
        if form.is_valid():
            call = form.save(commit=False)
            call.created_by = request.user
            call.save()
            messages.success(request, f"Funding call '{call.title}' published successfully.")
            return redirect('funding:detail', pk=call.pk)
    else:
        form = FundingCallForm()

    return render(request, 'funding/form.html', {
        'form': form,
        'action_title': 'Add Funding Call',
    })


@login_required
def funding_edit(request, pk):
    if not request.user.is_staff:
        raise PermissionDenied("Only Research Office staff can edit funding calls.")

    call = get_object_or_404(FundingCall, pk=pk)
    if request.method == 'POST':
        form = FundingCallForm(request.POST, instance=call)
        if form.is_valid():
            form.save()
            messages.success(request, f"Funding call '{call.title}' updated successfully.")
            return redirect('funding:detail', pk=call.pk)
    else:
        form = FundingCallForm(instance=call)

    return render(request, 'funding/form.html', {
        'form': form,
        'call': call,
        'action_title': f'Edit Funding Call: {call.title}',
    })


@login_required
@require_POST
def funding_watch(request, pk):
    call = get_object_or_404(FundingCall, pk=pk)
    if call.watchers.filter(pk=request.user.pk).exists():
        call.watchers.remove(request.user)
        messages.info(request, "Reminders turned off.")
    else:
        call.watchers.add(request.user)
        messages.success(request, "You'll get deadline reminders for this call.")

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('funding:detail', args=[pk])
    return redirect(next_url)
