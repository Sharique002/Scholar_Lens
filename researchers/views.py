from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone

from .models import ResearcherProfile, ResearchInterest, Skill, Department
from .forms import ResearcherProfileForm, ResearchInterestForm, SkillForm
from dashboard.models import ResearchActivity
from dashboard import audit


@login_required
def researcher_list(request):
    query = request.GET.get('q', '')
    availability = request.GET.get('availability', '')
    dept_id = request.GET.get('department', '')

    profiles = ResearcherProfile.objects.select_related('user', 'department').prefetch_related('interests', 'skills')

    if query:
        profiles = profiles.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__username__icontains=query) |
            Q(headline__icontains=query) |
            Q(expertise_summary__icontains=query)
        )

    if availability == 'true':
        profiles = profiles.filter(is_available_for_collaboration=True)
    elif availability == 'false':
        profiles = profiles.filter(is_available_for_collaboration=False)

    if dept_id:
        if dept_id.isdigit():
            profiles = profiles.filter(department_id=int(dept_id))
        else:
            profiles = profiles.filter(department__code__iexact=dept_id)

    paginator = Paginator(profiles.order_by('-created_at'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    departments = Department.objects.all()

    return render(request, 'researchers/list.html', {
        'page_obj': page_obj,
        'query': query,
        'availability': availability,
        'departments': departments,
        'selected_dept': dept_id,
    })


@login_required
def researcher_detail(request, pk):
    profile = get_object_or_404(
        ResearcherProfile.objects.select_related('user', 'department').prefetch_related('interests', 'skills'),
        pk=pk
    )

    papers = profile.user.uploaded_papers.all().order_by('-created_at')
    projects = profile.user.led_projects.all().order_by('-created_at')
    is_owner = (profile.user == request.user)

    return render(request, 'researchers/detail.html', {
        'profile': profile,
        'papers': papers,
        'projects': projects,
        'is_owner': is_owner,
    })


@login_required
def researcher_profile_edit(request):
    profile, created = ResearcherProfile.objects.get_or_create(user=request.user)
    old_dept_id = profile.department_id
    old_orcid = profile.orcid_id

    if request.method == 'POST':
        form = ResearcherProfileForm(request.POST, instance=profile)
        if form.is_valid():
            new_profile = form.save(commit=False)
            if profile.verification_status == 'VERIFIED':
                if new_profile.department_id != old_dept_id or new_profile.orcid_id != old_orcid:
                    new_profile.verification_status = 'UNVERIFIED'
                    new_profile.verified_by = None
                    new_profile.verified_at = None
                    messages.info(request, "Your profile changed, so please request verification again.")

            new_profile.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('researchers:detail', pk=profile.pk)
    else:
        form = ResearcherProfileForm(instance=profile)

    return render(request, 'researchers/edit_profile.html', {
        'form': form,
        'profile': profile
    })


@login_required
@require_POST
def request_verification(request):
    profile = get_object_or_404(ResearcherProfile, user=request.user)
    profile.verification_status = 'PENDING'
    profile.save(update_fields=['verification_status', 'updated_at'])

    staff_users = User.objects.filter(is_staff=True)
    actor_name = request.user.get_full_name() or request.user.username
    for staff in staff_users:
        ResearchActivity.objects.create(
            user=staff,
            activity_type='VERIFICATION',
            description=f"{actor_name} asked to verify their profile"
        )

    messages.success(request, "Verification request submitted. The Research Office will review your profile.")
    return redirect('researchers:detail', pk=profile.pk)


@login_required
def verification_queue(request):
    if not request.user.is_staff:
        raise PermissionDenied("Only Research Office staff can view the verification queue.")

    pending_profiles = ResearcherProfile.objects.filter(
        verification_status='PENDING'
    ).select_related('user', 'department').order_by('updated_at')

    return render(request, 'researchers/verification_queue.html', {
        'pending_profiles': pending_profiles,
        'pending_count': pending_profiles.count(),
    })


@login_required
@require_POST
def verify_researcher(request, pk):
    if not request.user.is_staff:
        raise PermissionDenied("Only Research Office staff can review verification requests.")

    profile = get_object_or_404(ResearcherProfile, pk=pk)
    action = request.POST.get('action')
    note = request.POST.get('note', '').strip()

    if action == 'approve':
        profile.verification_status = 'VERIFIED'
        profile.verified_by = request.user
        profile.verified_at = timezone.now()
        profile.verification_note = ''
        profile.save()

        audit.record(request.user, 'profile.verified', profile)
        ResearchActivity.objects.create(
            user=profile.user,
            activity_type='VERIFICATION',
            description="Your researcher profile was verified."
        )
        messages.success(request, f"Profile for {profile.user.username} approved and verified.")
    elif action == 'reject':
        profile.verification_status = 'REJECTED'
        profile.verified_by = request.user
        profile.verified_at = timezone.now()
        profile.verification_note = note
        profile.save()

        audit.record(request.user, 'profile.rejected', profile, note=note)
        desc = f"Your verification request was rejected: {note}" if note else "Your verification request was rejected."
        ResearchActivity.objects.create(
            user=profile.user,
            activity_type='VERIFICATION',
            description=desc
        )
        messages.warning(request, f"Profile verification for {profile.user.username} rejected.")

    return redirect('researchers:verification_queue')


@login_required
def researcher_add_interest(request):
    profile, created = ResearcherProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ResearchInterestForm(request.POST)
        if form.is_valid():
            interest, created = ResearchInterest.objects.get_or_create(
                name=form.cleaned_data['name'],
                defaults={
                    'category': form.cleaned_data['category'],
                    'parent': form.cleaned_data.get('parent')
                }
            )
            profile.interests.add(interest)
            messages.success(request, 'Interest added.')
            return redirect('researchers:edit_profile')
    return redirect('researchers:edit_profile')


@login_required
def researcher_remove_interest(request, pk):
    profile = get_object_or_404(ResearcherProfile, user=request.user)
    if request.method == 'POST':
        interest = get_object_or_404(ResearchInterest, pk=pk)
        profile.interests.remove(interest)
        messages.success(request, 'Interest removed.')
    return redirect('researchers:edit_profile')


@login_required
def researcher_add_skill(request):
    profile, created = ResearcherProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill, created = Skill.objects.get_or_create(
                name=form.cleaned_data['name'],
                defaults={'category': form.cleaned_data['category']}
            )
            profile.skills.add(skill)
            messages.success(request, 'Skill added.')
            return redirect('researchers:edit_profile')
    return redirect('researchers:edit_profile')
