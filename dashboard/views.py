"""Dashboard views for Scholar Lens."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from .models import ResearchActivity
from papers.models import ResearchPaper
from projects.models import ProjectMember, ResearchProject
from ai_engine.models import AIAnalysis
from evaluation.models import EvaluationReport
from collaboration.models import CollaborationRequest


def landing_page(request):
    """Public landing page."""
    return render(request, 'dashboard/landing.html')


from django.db.models import Avg, Q

@login_required
def dashboard_view(request):
    """Main user dashboard with research intelligence overview and optimized queries."""
    user = request.user

    # Paper statistics & query optimization
    user_papers_qs = ResearchPaper.objects.filter(uploader=user)
    total_papers = user_papers_qs.count()
    recent_papers = user_papers_qs.prefetch_related('authors').order_by('-created_at')[:5]

    # Research area distribution for chart
    areas = (
        user_papers_qs
        .values('research_area')
        .annotate(count=Count('id'))
    )
    research_areas_data = {
        area['research_area'] or 'General': area['count'] for area in areas
    }

    # Project statistics
    total_projects = ProjectMember.objects.filter(user=user).count()

    # AI analysis & gap statistics
    ai_analyses = AIAnalysis.objects.filter(paper__uploader=user).count()
    from ai_engine.models import ResearchGap
    total_gaps = ResearchGap.objects.filter(paper__uploader=user).count()
    top_gaps = ResearchGap.objects.filter(paper__uploader=user).select_related('paper')[:4]

    # Research Strength metrics
    eval_reports_qs = EvaluationReport.objects.filter(paper__uploader=user)
    evaluation_reports = eval_reports_qs.count()
    avg_score_val = eval_reports_qs.aggregate(Avg('overall_score'))['overall_score__avg']
    avg_eval_score = round(avg_score_val, 1) if avg_score_val is not None else None
    top_evaluated_report = eval_reports_qs.select_related('paper').order_by('-overall_score').first()

    # Collaboration statistics & network size
    pending_collaborations = CollaborationRequest.objects.filter(
        receiver=user, status='PENDING'
    ).count()
    user_project_ids = ResearchProject.objects.filter(
        Q(leader=user) | Q(members__user=user)
    ).values_list('id', flat=True)
    total_collaborators = ProjectMember.objects.filter(
        project_id__in=user_project_ids
    ).exclude(user=user).values('user').distinct().count()

    # Recent activity with related paper pre-fetching
    recent_activities = ResearchActivity.objects.filter(user=user).select_related('related_paper')[:10]

    # Latest external research & emerging technologies from Google Scholar
    latest_external_papers = ResearchPaper.objects.filter(
        is_external=True
    ).prefetch_related('authors').order_by('-publication_date', '-created_at')[:4]

    context = {
        **_dashboard_overview(user),
        'total_papers': total_papers,
        'total_projects': total_projects,
        'ai_analyses': ai_analyses,
        'total_gaps': total_gaps,
        'top_gaps': top_gaps,
        'evaluation_reports': evaluation_reports,
        'avg_eval_score': avg_eval_score,
        'top_evaluated_report': top_evaluated_report,
        'total_collaborators': total_collaborators,
        'pending_collaborations': pending_collaborations,
        'recent_activities': recent_activities,
        'recent_papers': recent_papers,
        'latest_external_papers': latest_external_papers,
        'research_areas_data': research_areas_data,
    }
    return render(request, 'dashboard/home.html', context)


def _dashboard_overview(user):
    """Institution summary, deadlines, risks and recommendations for the dashboard.
    Everything is read from the database and limited to what this user may see."""
    from datetime import timedelta
    from django.db.models import IntegerField
    from django.db.models.functions import Coalesce, ExtractYear
    from django.urls import reverse
    from django.utils import timezone
    from facilities.models import Booking
    from funding.models import FundingCall
    from opportunities.models import ResearchOpening
    from projects.models import Milestone
    from researchers.models import ResearcherProfile
    from collaboration.models import CollaborationSuggestion

    now = timezone.now()
    today = timezone.localdate()
    horizon = today + timedelta(days=30)

    my_project_ids = list(
        ResearchProject.objects.filter(Q(leader=user) | Q(members__user=user)).values_list('id', flat=True).distinct()
    )
    visible_projects = ResearchProject.objects.filter(Q(is_public=True) | Q(id__in=my_project_ids))
    open_openings = ResearchOpening.objects.filter(status='OPEN').filter(Q(deadline__isnull=True) | Q(deadline__gte=today))
    open_funding = FundingCall.objects.filter(is_published=True, deadline__gte=now)

    summary = {
        'researchers': ResearcherProfile.objects.count(),
        'publications': ResearchPaper.objects.filter(is_external=False).count(),
        'active_projects': visible_projects.filter(status='ACTIVE').count(),
        'open_openings': open_openings.count(),
        'my_bookings': Booking.objects.filter(
            user=user, status__in=['PENDING', 'APPROVED'], during__endswith__gte=now
        ).count(),
        'open_funding': open_funding.count(),
    }

    # Institutional publications per year (last 8 years that have data).
    years = (
        ResearchPaper.objects.filter(is_external=False)
        .annotate(pub_year=Coalesce('year', ExtractYear('publication_date'), ExtractYear('created_at'), output_field=IntegerField()))
        .values('pub_year').annotate(count=Count('id')).order_by('pub_year')
    )
    years = [y for y in years if y['pub_year'] and y['pub_year'] <= today.year][-8:]
    publication_trend = {'labels': [str(y['pub_year']) for y in years], 'values': [y['count'] for y in years]}

    # Upcoming deadlines over the next 30 days, merged across modules.
    deadlines = []
    for call in open_funding.filter(deadline__lte=now + timedelta(days=30)).order_by('deadline')[:5]:
        deadlines.append({'date': timezone.localdate(call.deadline), 'title': call.title, 'kind': 'Funding call',
                          'icon': 'bi-cash-coin', 'url': reverse('funding:detail', args=[call.pk])})
    for op in open_openings.filter(deadline__isnull=False, deadline__lte=horizon).order_by('deadline')[:5]:
        deadlines.append({'date': op.deadline, 'title': op.title, 'kind': 'Research opening',
                          'icon': 'bi-briefcase', 'url': reverse('opportunities:detail', args=[op.pk])})
    for m in (Milestone.objects.filter(project_id__in=my_project_ids, status__in=['PLANNED', 'IN_PROGRESS'],
                                       due_date__gte=today, due_date__lte=horizon)
              .select_related('project').order_by('due_date')[:5]):
        deadlines.append({'date': m.due_date, 'title': m.title, 'kind': f'Milestone · {m.project.title}',
                          'icon': 'bi-flag', 'url': reverse('projects:milestones', args=[m.project_id])})
    deadlines.sort(key=lambda d: d['date'])
    for d in deadlines:
        d['days_left'] = (d['date'] - today).days

    at_risk = Milestone.objects.filter(risk__in=['AT_RISK', 'OVERDUE'], status__in=['PLANNED', 'IN_PROGRESS'])
    if not user.is_staff:
        at_risk = at_risk.filter(project_id__in=my_project_ids)
    at_risk = at_risk.select_related('project').order_by('due_date')[:5]

    profile = ResearcherProfile.objects.filter(user=user).first()
    suggestions = []
    relevant_openings = open_openings.select_related('department').order_by('deadline', '-created_at')
    if profile:
        suggestions = (CollaborationSuggestion.objects.filter(researcher=profile, is_dismissed=False)
                       .select_related('suggested__user', 'suggested__department').order_by('-score')[:3])
        relevant_openings = relevant_openings.annotate(
            skill_matches=Count('required_skills', filter=Q(required_skills__researchers=profile), distinct=True)
        ).order_by('-skill_matches', 'deadline', '-created_at')

    return {
        'summary': summary,
        'publication_trend': publication_trend,
        'publication_trend_rows': list(zip(publication_trend['labels'], publication_trend['values'])),
        'upcoming_deadlines': deadlines[:6],
        'at_risk_milestones': at_risk,
        'collab_suggestions': suggestions,
        'relevant_openings': relevant_openings[:3],
    }


@login_required
def notifications_view(request):
    """Notifications page showing pending requests and activities."""
    user = request.user
    pending_requests = CollaborationRequest.objects.filter(
        receiver=user, status='PENDING'
    ).select_related('sender')
    recent_activities = ResearchActivity.objects.filter(user=user)[:20]

    context = {
        'pending_requests': pending_requests,
        'recent_activities': recent_activities,
    }
    return render(request, 'dashboard/notifications.html', context)


@login_required
def settings_view(request):
    """User settings page."""
    return render(request, 'dashboard/settings.html')


@login_required
def office_hub(request):
    """Unified Research Office administrative and governance hub."""
    from analytics.metrics import is_dean
    if not (request.user.is_staff or is_dean(request.user)):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Only Research Office staff and institutional executives can access this hub.")

    from researchers.models import ResearcherProfile
    from papers.models import DuplicateCandidate, PaperAuthor
    from projects.models import Milestone
    from facilities.models import Booking
    from dashboard.models import AuditEntry

    pending_verifications_count = ResearcherProfile.objects.filter(verification_status='PENDING').count()
    pending_duplicates_count = DuplicateCandidate.objects.filter(status='PENDING').count()
    pending_authors_count = PaperAuthor.objects.filter(match_status='PENDING_REVIEW').count()
    at_risk_milestones_count = Milestone.objects.filter(risk__in=['AT_RISK', 'OVERDUE'], status__in=['PLANNED', 'IN_PROGRESS']).count()
    pending_bookings_count = Booking.objects.filter(status='PENDING').count()

    recent_audits = AuditEntry.objects.select_related('actor').order_by('-created_at')[:15]

    return render(request, 'dashboard/office.html', {
        'pending_verifications_count': pending_verifications_count,
        'pending_duplicates_count': pending_duplicates_count,
        'pending_authors_count': pending_authors_count,
        'at_risk_milestones_count': at_risk_milestones_count,
        'pending_bookings_count': pending_bookings_count,
        'recent_audits': recent_audits,
    })


def privacy_policy(request):
    """Public privacy policy page for Google OAuth compliance."""
    return render(request, 'dashboard/privacy.html')


def terms_of_service(request):
    """Public terms of service page."""
    return render(request, 'dashboard/terms.html')


def error_404(request, exception):
    """Custom 404 error page."""
    return render(request, 'errors/404.html', status=404)


def error_403(request, exception):
    """Custom 403 error page."""
    return render(request, 'errors/403.html', status=403)


def error_500(request):
    """Custom 500 error page; the traceback is never shown outside DEBUG."""
    from scholar_lens.middleware import render_server_error
    return render_server_error(request)



def healthz(request):
    """Liveness/readiness probe for the platform (Render healthCheckPath): 200 if the DB answers."""
    from django.db import connection
    from django.http import JsonResponse
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    except Exception:  # noqa: BLE001
        import logging
        logging.getLogger(__name__).exception("health check: database unavailable")
        return JsonResponse({'status': 'error', 'database': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok', 'database': 'ok'})
