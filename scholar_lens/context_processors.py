"""Context processors for scholar_lens project."""
from django.conf import settings


def site_settings(request):
    """Make site settings and live research marquee items available in all templates."""
    marquee_items = []
    try:
        from papers.models import ResearchPaper
        # Retrieve latest research papers ordered by actual publication date (falling back to created_at)
        recent_papers = list(
            ResearchPaper.objects.prefetch_related('authors')
            .order_by('-publication_date', '-created_at')[:8]
        )

        if recent_papers:
            for p in recent_papers:
                year_str = f" ({p.publication_date.year})" if p.publication_date else ""
                area_label = p.get_research_area_display()
                first_author = p.authors.first()
                author_suffix = f" — {first_author.name}" if first_author else ""

                if p.is_external:
                    marquee_items.append(f"✦ LATEST RESEARCH: {p.title[:65]}{year_str}{author_suffix}")
                else:
                    marquee_items.append(f"✦ NEW PAPER: {p.title[:65]}{year_str}")

                if p.research_area and p.research_area != 'OTHER':
                    marquee_items.append(f"✦ EMERGING TECHNOLOGY: {area_label} Innovation")

                if p.keywords:
                    first_kw = p.keywords.split(',')[0].strip()
                    if first_kw:
                        marquee_items.append(f"✦ RESEARCH TREND: {first_kw} in {area_label}")
    except Exception:
        marquee_items = []

    # Baseline fallback if database is brand new or empty
    if not marquee_items:
        marquee_items = [
            "✦ SCHOLAR LENS RESEARCH INTELLIGENCE",
            "✦ 7-DIMENSION NOVELTY EVALUATION ENGINE",
            "✦ GOOGLE SCHOLAR COMPARATIVE RADAR",
            "✦ CONTEXTUAL RAG PAPER ASSISTANT",
            "✦ AI RESEARCH GAP DETECTOR",
            "✦ SEMANTIC VECTOR SEARCH",
        ]

    return {
        'SITE_NAME': settings.SITE_NAME,
        'AI_CONFIGURED': bool(settings.OPENAI_API_KEY),
        'marquee_items': marquee_items,
    }

