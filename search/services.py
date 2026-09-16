import datetime
import logging
import numpy as np
from django.db.models import Q
from django.utils import timezone
from papers.models import ResearchPaper, PaperChunk, PaperEmbedding
from ai_engine.services import AIService, cosine_similarity

logger = logging.getLogger('scholar_lens')


class HybridSearchEngine:
    """
    Transparent Hybrid Academic Search Engine.
    Combines:
      - 60% Semantic Vector Similarity
      - 25% Lexical TF Relevance
      - 10% Research Area Match
      - 05% Recency Decay
    """

    WEIGHT_SEMANTIC = 0.60
    WEIGHT_LEXICAL = 0.25
    WEIGHT_AREA = 0.10
    WEIGHT_RECENCY = 0.05

    def search(
        self,
        query: str,
        research_area: str = None,
        year: int = None,
        author: str = None,
        threshold: float = None,
        use_semantic: bool = True,
        limit: int = 50,
        area: str = None,
    ) -> list:
        research_area = research_area or area
        papers_qs = ResearchPaper.objects.all().prefetch_related('authors')

        if research_area:
            papers_qs = papers_qs.filter(research_area=research_area)

        if year:
            papers_qs = papers_qs.filter(created_at__year=year)

        if author:
            papers_qs = papers_qs.filter(
                Q(authors__name__icontains=author) | Q(uploader__username__icontains=author)
            ).distinct()

        if not query:
            # If no query string, sort by recency
            results = []
            for p in papers_qs.order_by('-created_at')[:limit]:
                breakdown = {'semantic': 0.0, 'lexical': 0.0, 'area': 100.0 if research_area else 0.0, 'recency': 100.0, 'final_score': 100.0}
                results.append({
                    'paper': p,
                    'score': 100.0,
                    'score_breakdown': breakdown,
                    'breakdown': breakdown,
                    'match_percentage': 100.0,
                })
            return results

        q_lower = query.lower()
        q_words = [w for w in q_lower.split() if len(w) > 2]
        current_year = timezone.now().year

        ai = AIService()
        query_emb = None
        if use_semantic and ai.is_configured:
            try:
                query_emb = ai.generate_embedding(query)
            except Exception as e:
                logger.warning(f"Failed to generate query embedding: {e}")

        scored_papers = []

        for paper in papers_qs:
            # 1. Semantic Component (0.60 weight)
            s_sem = 0.0
            if query_emb is not None:
                # Find max chunk similarity
                chunk_embs = PaperEmbedding.objects.filter(chunk__paper=paper)
                if chunk_embs.exists():
                    sims = [cosine_similarity(query_emb, ce.embedding) for ce in chunk_embs]
                    s_sem = max(sims) if sims else 0.0
            elif q_words:
                # Lexical semantic proxy when vector engine is offline
                paper_text = f"{paper.title} {paper.abstract} {paper.keywords}".lower()
                chunk_texts = list(PaperChunk.objects.filter(paper=paper).values_list('content', flat=True)[:5])
                combined = (paper_text + " " + " ".join(chunk_texts)).lower()
                matched = sum(1 for w in q_words if w in combined)
                s_sem = min(1.0, matched / max(len(q_words), 1))

            # 2. Lexical Component (0.25 weight)
            title_lower = (paper.title or '').lower()
            abstract_lower = (paper.abstract or '').lower()
            keywords_lower = (paper.keywords or '').lower()

            title_matches = sum(1 for w in q_words if w in title_lower)
            abstract_matches = sum(1 for w in q_words if w in abstract_lower)
            keyword_matches = sum(1 for w in q_words if w in keywords_lower)

            lex_raw = (title_matches * 3) + (keyword_matches * 2) + abstract_matches
            max_lex_possible = max(len(q_words) * 3, 1)
            s_lex = min(1.0, lex_raw / max_lex_possible)

            # 3. Research Area Component (0.10 weight)
            s_area = 0.0
            if research_area and paper.research_area == research_area:
                s_area = 1.0
            elif any(w in (paper.get_research_area_display() or '').lower() for w in q_words):
                s_area = 0.8
            elif paper.research_area:
                s_area = 0.4

            # 4. Recency Component (0.05 weight)
            p_date = getattr(paper, 'publication_date', None) or paper.created_at
            p_year = p_date.year if hasattr(p_date, 'year') else (paper.created_at.year if paper.created_at else current_year)
            age_years = max(0, current_year - p_year)
            s_rec = max(0.2, 1.0 - (age_years * 0.1))

            # Only include papers that have at least some relevance match
            if s_sem > 0.15 or s_lex > 0.1 or (not q_words and s_area > 0):
                final_score = (
                    0.60 * s_sem +
                    0.25 * s_lex +
                    0.10 * s_area +
                    0.05 * s_rec
                )
                score_pct = round(final_score * 100.0, 1)

                if threshold is None or score_pct >= threshold:
                    b_down = {
                        'semantic': round(s_sem * 100.0, 1),
                        'lexical': round(s_lex * 100.0, 1),
                        'area': round(s_area * 100.0, 1),
                        'recency': round(s_rec * 100.0, 1),
                        'final_score': score_pct,
                    }
                    scored_papers.append({
                        'paper': paper,
                        'score': score_pct,
                        'score_raw': final_score,
                        'match_percentage': score_pct,
                        'score_breakdown': b_down,
                        'breakdown': b_down,
                    })

        scored_papers.sort(key=lambda x: x['score_raw'], reverse=True)
        return scored_papers[:limit]
