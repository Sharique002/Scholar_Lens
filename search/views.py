from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q

from papers.models import ResearchPaper
from .forms import SearchForm
from .services import HybridSearchEngine


@login_required
def search_view(request):
    """Faceted hybrid search view for academic literature."""
    form = SearchForm(request.GET)
    query = request.GET.get('q', '').strip()
    research_area = request.GET.get('research_area', '').strip()
    year_str = request.GET.get('year', '').strip()
    author = request.GET.get('author', '').strip()
    threshold_str = request.GET.get('threshold', '').strip()
    use_semantic = request.GET.get('semantic') not in ('off', 'false', '0')

    year = int(year_str) if year_str.isdigit() else None
    try:
        threshold = float(threshold_str) if threshold_str else None
    except ValueError:
        threshold = None

    search_type = 'Hybrid (Semantic 60% + Lexical 25% + Area 10% + Recency 5%)'
    results = []

    if query or research_area or year or author:
        engine = HybridSearchEngine()
        results = engine.search(
            query=query,
            research_area=research_area if research_area else None,
            year=year,
            author=author if author else None,
            threshold=threshold,
            use_semantic=use_semantic,
            limit=100
        )
    else:
        # Default browse view
        papers = ResearchPaper.objects.all().prefetch_related('authors').order_by('-created_at')[:40]
        results = [{'paper': p, 'score': None, 'score_breakdown': None} for p in papers]

    # Pagination
    paginator = Paginator(results, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'form': form,
        'query': query,
        'current_area': research_area,
        'current_year': year,
        'current_author': author,
        'current_threshold': threshold,
        'search_type': search_type,
        'page_obj': page_obj,
        'total_results': len(results),
    }

    return render(request, 'search/search.html', context)



from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import models
from django.db.models import Count
from researchers.models import ResearcherProfile, Department, ResearchInterest


@login_required
def expertise_search(request):
    """Faceted full-text expertise search across researcher profiles."""
    query = request.GET.get('q', '').strip()
    selected_dept = request.GET.get('department', '').strip()
    selected_avail = request.GET.get('availability', '').strip()
    selected_interest = request.GET.get('interest', '').strip()

    profiles = (
        ResearcherProfile.objects
        .select_related('user', 'department')
        .prefetch_related('interests', 'skills')
    )

    if query:
        search_query = SearchQuery(query)
        profiles = (
            profiles
            .filter(search_document=search_query)
            .annotate(rank=SearchRank(models.F('search_document'), search_query))
            .order_by('-rank', '-created_at')
        )
    else:
        profiles = profiles.order_by('-created_at')

    # Apply faceted filters
    if selected_dept:
        if selected_dept.isdigit():
            profiles = profiles.filter(department_id=int(selected_dept))
        else:
            profiles = profiles.filter(department__code__iexact=selected_dept)

    if selected_avail == 'true':
        profiles = profiles.filter(is_available_for_collaboration=True)
    elif selected_avail == 'false':
        profiles = profiles.filter(is_available_for_collaboration=False)

    if selected_interest:
        profiles = profiles.filter(interests__name__iexact=selected_interest)

    dept_facets = Department.objects.annotate(
        profile_count=Count('researchers')
    ).filter(profile_count__gt=0).order_by('-profile_count')

    interest_facets = ResearchInterest.objects.annotate(
        profile_count=Count('researchers')
    ).filter(profile_count__gt=0).order_by('-profile_count')[:15]

    available_count = ResearcherProfile.objects.filter(is_available_for_collaboration=True).count()
    busy_count = ResearcherProfile.objects.filter(is_available_for_collaboration=False).count()

    paginator = Paginator(profiles, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'selected_dept': selected_dept,
        'selected_avail': selected_avail,
        'selected_interest': selected_interest,
        'dept_facets': dept_facets,
        'interest_facets': interest_facets,
        'available_count': available_count,
        'busy_count': busy_count,
    }
    return render(request, 'search/expertise.html', context)
