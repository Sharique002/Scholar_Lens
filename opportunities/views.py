from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from .models import ResearchOpening, OpportunityApplication
from .forms import ResearchOpeningForm, OpportunityApplicationForm
from projects.models import ProjectMember
from dashboard.audit import record as audit_record


def openings_list(request):
    q = request.GET.get('q', '').strip()
    dept = request.GET.get('department', '').strip()
    status_filter = request.GET.get('status', 'OPEN').strip()

    qs = ResearchOpening.objects.select_related('project', 'department', 'created_by').prefetch_related('required_skills')

    if status_filter:
        qs = qs.filter(status=status_filter)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if dept:
        qs = qs.filter(department__name__icontains=dept)

    recommended_openings = []
    if request.user.is_authenticated and hasattr(request.user, 'researcher_profile'):
        user_skills = set(request.user.researcher_profile.skills.all())
        for op in qs.filter(status='OPEN'):
            op_skills = set(op.required_skills.all())
            if op_skills:
                match_count = len(user_skills & op_skills)
                pct = int((match_count / len(op_skills)) * 100)
            else:
                pct = 100 if user_skills else 50
            if pct > 0:
                op.match_pct = pct
                recommended_openings.append(op)
        recommended_openings.sort(key=lambda x: getattr(x, 'match_pct', 0), reverse=True)

    return render(request, 'opportunities/list.html', {
        'openings': qs,
        'recommended_openings': recommended_openings,
        'q': q,
        'dept': dept,
        'status_filter': status_filter,
    })


def opening_detail(request, pk):
    opening = get_object_or_404(
        ResearchOpening.objects.select_related('project', 'department', 'created_by').prefetch_related('required_skills'),
        pk=pk
    )

    is_manager = False
    if request.user.is_authenticated:
        is_manager = (
            request.user == opening.created_by or
            (opening.project and request.user == opening.project.leader) or
            request.user.is_staff
        )

    user_application = None
    if request.user.is_authenticated:
        user_application = OpportunityApplication.objects.filter(opening=opening, applicant=request.user).first()

    applications = []
    if is_manager:
        applications = opening.applications.select_related('applicant').order_by('-created_at')

    apply_form = None
    if request.user.is_authenticated and not user_application and opening.status == 'OPEN':
        apply_form = OpportunityApplicationForm()

    return render(request, 'opportunities/detail.html', {
        'opening': opening,
        'is_manager': is_manager,
        'user_application': user_application,
        'applications': applications,
        'apply_form': apply_form,
    })


@login_required
def opening_create(request):
    if request.method == 'POST':
        form = ResearchOpeningForm(request.POST)
        if form.is_valid():
            opening = form.save(commit=False)
            opening.created_by = request.user
            opening.save()
            form.save_m2m()
            messages.success(request, f"Opportunity '{opening.title}' posted successfully.")
            return redirect('opportunities:detail', pk=opening.pk)
    else:
        form = ResearchOpeningForm()

    return render(request, 'opportunities/form.html', {'form': form, 'title': 'Post Research Opening'})


@login_required
def opening_apply(request, pk):
    opening = get_object_or_404(ResearchOpening, pk=pk)

    if opening.status != 'OPEN':
        messages.error(request, "This opportunity is closed.")
        return redirect('opportunities:detail', pk=pk)

    if opening.deadline and opening.deadline < timezone.now().date():
        messages.error(request, "The deadline for this opportunity has passed.")
        return redirect('opportunities:detail', pk=pk)

    if request.user == opening.created_by or (opening.project and request.user == opening.project.leader):
        messages.error(request, "You cannot apply to an opportunity you manage.")
        return redirect('opportunities:detail', pk=pk)

    if OpportunityApplication.objects.filter(opening=opening, applicant=request.user).exists():
        messages.info(request, "You have already applied to this opportunity.")
        return redirect('opportunities:detail', pk=pk)

    if request.method == 'POST':
        form = OpportunityApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.opening = opening
            app.applicant = request.user
            app.save()

            audit_record(
                actor=request.user,
                action='application_submitted',
                target=app,
                opening_id=opening.id
            )
            messages.success(request, "Your application has been submitted successfully.")
            return redirect('opportunities:detail', pk=pk)
        else:
            # Re-render detail view with form errors
            return render(request, 'opportunities/detail.html', {
                'opening': opening,
                'apply_form': form,
                'user_application': None,
                'is_manager': False,
                'applications': [],
            })

    return redirect('opportunities:detail', pk=pk)


@login_required
def application_review(request, pk, action):
    app = get_object_or_404(OpportunityApplication.objects.select_related('opening__project'), pk=pk)
    opening = app.opening

    is_authorized = (
        request.user == opening.created_by or
        (opening.project and request.user == opening.project.leader) or
        request.user.is_staff
    )

    if not is_authorized:
        raise PermissionDenied("You do not have permission to review this application.")

    if request.method == 'POST':
        if action == 'shortlist':
            app.status = 'SHORTLISTED'
            app.reviewed_by = request.user
            app.reviewed_at = timezone.now()
            app.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])

            audit_record(
                actor=request.user,
                action='application_shortlisted',
                target=app,
                opening_id=opening.id
            )
            messages.success(request, f"Application by {app.applicant.username} shortlisted.")
        elif action == 'accept':
            app.status = 'ACCEPTED'
            app.reviewed_by = request.user
            app.reviewed_at = timezone.now()
            app.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])

            accepted_count = opening.applications.filter(status='ACCEPTED').count()
            if accepted_count >= opening.spots_available:
                opening.status = 'CLOSED'
                opening.save(update_fields=['status'])

            if opening.project:
                ProjectMember.objects.get_or_create(
                    project=opening.project,
                    user=app.applicant,
                    defaults={'role': 'RESEARCHER'}
                )

            audit_record(
                actor=request.user,
                action='application_accepted',
                target=app,
                opening_id=opening.id
            )
            messages.success(request, f"Application by {app.applicant.username} accepted. Position filled.")
        elif action == 'reject':
            app.status = 'REJECTED'
            app.reviewed_by = request.user
            app.reviewed_at = timezone.now()
            app.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])

            audit_record(
                actor=request.user,
                action='application_rejected',
                target=app,
                opening_id=opening.id
            )
            messages.info(request, f"Application by {app.applicant.username} declined.")

    return redirect('opportunities:detail', pk=opening.pk)


@login_required
@require_POST
def application_withdraw(request, pk):
    app = get_object_or_404(OpportunityApplication, pk=pk, applicant=request.user)
    opening_pk = app.opening.pk
    app.delete()
    messages.success(request, "Your application has been withdrawn.")
    return redirect('opportunities:detail', pk=opening_pk)
