"""Read-only JSON API for the P08 resources (spec section 8)."""
from functools import wraps

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Q
from django.http import JsonResponse
from django.urls import path
from django.utils import timezone

from analytics.metrics import compute_academic_year_metrics, get_academic_year_range, is_dean
from facilities.models import Booking, Facility
from funding.models import FundingCall
from opportunities.models import ResearchOpening
from papers.models import ResearchPaper
from projects.models import ResearchProject
from researchers.models import ResearcherProfile

MAX_LIMIT = 100


def api_login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'authentication required'}, status=401)
        return view(request, *args, **kwargs)
    return wrapper


def _limit(request):
    try:
        return max(1, min(int(request.GET.get('limit', 50)), MAX_LIMIT))
    except ValueError:
        return 50


def _researcher(p):
    return {
        'id': p.pk,
        'username': p.user.username,
        'name': p.user.get_full_name() or p.user.username,
        'department': p.department.name if p.department else None,
        'headline': p.headline,
        'orcid_id': p.orcid_id,
        'scopus_id': p.scopus_id,
        'verification_status': p.verification_status,
        'available_for_collaboration': p.is_available_for_collaboration,
        'interests': [i.name for i in p.interests.all()],
        'skills': [s.name for s in p.skills.all()],
    }


def _profiles():
    return ResearcherProfile.objects.select_related('user', 'department').prefetch_related('interests', 'skills')


@api_login_required
def researchers(request):
    qs = _profiles().order_by('user__username')
    if request.GET.get('department'):
        qs = qs.filter(department__code__iexact=request.GET['department'])
    return JsonResponse({'results': [_researcher(p) for p in qs[:_limit(request)]]})


@api_login_required
def expertise_search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'error': 'q is required'}, status=400)
    sq = SearchQuery(query)
    qs = (
        _profiles()
        .filter(search_document=sq)
        .annotate(rank=SearchRank(F('search_document'), sq))
        .order_by('-rank')
    )
    if request.GET.get('department'):
        qs = qs.filter(department__code__iexact=request.GET['department'])
    return JsonResponse({
        'query': query,
        'results': [{**_researcher(p), 'rank': round(p.rank, 4)} for p in qs[:_limit(request)]],
    })


@api_login_required
def publications(request):
    qs = ResearchPaper.objects.order_by('-year', '-created_at')
    if request.GET.get('year', '').isdigit():
        qs = qs.filter(year=int(request.GET['year']))
    data = [{
        'id': p.pk,
        'title': p.title,
        'year': p.year,
        'venue': p.venue,
        'doi': p.doi,
        'pub_type': p.pub_type,
        'source': p.source,
        'authors': [a.name for a in p.authors.all()],
    } for p in qs.prefetch_related('authors')[:_limit(request)]]
    return JsonResponse({'results': data})


@api_login_required
def openings(request):
    qs = ResearchOpening.objects.filter(status='OPEN').select_related('department').prefetch_related('required_skills')
    data = [{
        'id': o.pk,
        'title': o.title,
        'department': o.department.name if o.department else None,
        'project_id': o.project_id,
        'required_skills': [s.name for s in o.required_skills.all()],
        'spots_available': o.spots_available,
        'deadline': o.deadline,
    } for o in qs[:_limit(request)]]
    return JsonResponse({'results': data})


@api_login_required
def projects(request):
    u = request.user
    qs = ResearchProject.objects.select_related('leader')
    if not u.is_staff:
        qs = qs.filter(Q(is_public=True) | Q(leader=u) | Q(members__user=u)).distinct()
    data = [{
        'id': p.pk,
        'title': p.title,
        'leader': p.leader.username,
        'status': p.status,
        'research_area': p.research_area,
        'start_date': p.start_date,
        'end_date': p.end_date,
        'milestones': [{
            'id': m.pk, 'title': m.title, 'due_date': m.due_date,
            'status': m.status, 'progress': m.progress, 'risk': m.risk,
        } for m in p.milestones.all()],
    } for p in qs.prefetch_related('milestones')[:_limit(request)]]
    return JsonResponse({'results': data})


@api_login_required
def facilities(request):
    qs = Facility.objects.filter(is_active=True).prefetch_related('slots')
    data = [{
        'id': f.pk,
        'name': f.name,
        'kind': f.kind,
        'department': f.department,
        'location': f.location,
        'capacity': f.capacity,
        'requires_approval': f.requires_approval,
        'opening_hours': [
            {'weekday': s.weekday, 'opens': s.opens, 'closes': s.closes} for s in f.slots.all()
        ],
    } for f in qs[:_limit(request)]]
    return JsonResponse({'results': data})


@api_login_required
def bookings(request):
    qs = Booking.objects.select_related('facility', 'user')
    if not request.user.is_staff:
        qs = qs.filter(Q(user=request.user) | Q(facility__custodian=request.user))
    data = [{
        'id': b.pk,
        'facility': b.facility.name,
        'user': b.user.username,
        'start': b.start,
        'end': b.end,
        'status': b.status,
        'purpose': b.purpose,
    } for b in qs[:_limit(request)]]
    return JsonResponse({'results': data})


@api_login_required
def funding_calls(request):
    now = timezone.now()
    qs = FundingCall.objects.filter(is_published=True).order_by('deadline')
    if request.GET.get('open') == 'true':
        qs = qs.filter(deadline__gte=now)
    data = [{
        'id': c.pk,
        'title': c.title,
        'sponsor': c.sponsor,
        'research_area': c.research_area,
        'amount': c.amount,
        'deadline': c.deadline,
        'state': c.state(),
        'url': c.url,
    } for c in qs[:_limit(request)]]
    return JsonResponse({'results': data})


@api_login_required
def research_analytics(request):
    u = request.user
    if not (u.is_staff or is_dean(u)):
        return JsonResponse({'error': 'Research Office or Dean of Research only'}, status=403)
    start, end, label = get_academic_year_range(request.GET.get('year', '').strip())
    # Per-researcher productivity is Dean-only (spec section 10).
    data = compute_academic_year_metrics(start, end, include_researchers=is_dean(u))
    return JsonResponse({'academic_year': label, **data})


urlpatterns = [
    path('researchers/', researchers, name='api_researchers'),
    path('publications/', publications, name='api_publications'),
    path('search/expertise/', expertise_search, name='api_search_expertise'),
    path('openings/', openings, name='api_openings'),
    path('projects/', projects, name='api_projects'),
    path('facilities/', facilities, name='api_facilities'),
    path('bookings/', bookings, name='api_bookings'),
    path('funding-calls/', funding_calls, name='api_funding_calls'),
    path('analytics/research/', research_analytics, name='api_analytics_research'),
]
