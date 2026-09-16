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


def error_404(request, exception):
    """Custom 404 error page."""
    return render(request, 'errors/404.html', status=404)


def error_403(request, exception):
    """Custom 403 error page."""
    return render(request, 'errors/403.html', status=403)


def error_500(request):
    """Custom 500 error page."""
    return render(request, 'errors/500.html', status=500)
