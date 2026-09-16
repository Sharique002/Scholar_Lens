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

