"""
Google Scholar and Academic Research Integration Service for Scholar Lens.
Handles server-side API integration, search query formulation, metadata normalization,
defensive error handling, and idempotent deduplication.
"""

import re
import datetime
import logging
import hashlib
from typing import List, Dict, Optional, Any
import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from papers.models import ResearchPaper, PaperAuthor, PaperChunk

logger = logging.getLogger('scholar_lens')


class GoogleScholarService:
    """
    Robust server-side Google Scholar integration service.
    Follows: Google Scholar -> API Provider -> Scholar_Lens backend -> Existing Paper System.
    """

    def __init__(self, api_key: Optional[str] = None, timeout: Optional[int] = None):
        self.api_key = api_key or getattr(settings, 'SERPAPI_API_KEY', '')
        self.timeout = timeout or getattr(settings, 'SCHOLAR_API_TIMEOUT', 10)
        self.max_results = getattr(settings, 'SCHOLAR_MAX_RESULTS', 5)

    @property
    def is_configured(self) -> bool:
        """Check if external Google Scholar API provider credentials exist."""
        return bool(self.api_key and self.api_key.strip())

    def generate_search_queries(self, paper: ResearchPaper) -> List[str]:
        """
        Extract meaningful search queries from a paper's title, abstract, keywords, and research area.
        Returns prioritized list of query strings.
        """
        queries = []

        # 1. Cleaned Title Query (strips non-alphanumeric noise, quotes exact title)
        clean_title = re.sub(r'[\r\n\t]+', ' ', paper.title or '').strip()
        # Remove common file extensions or trailing markers
        clean_title = re.sub(r'\.(pdf|docx?|txt)$', '', clean_title, flags=re.IGNORECASE).strip()
        if clean_title:
            queries.append(clean_title)

        # 2. Key concepts & keywords query
        keywords_list = [k.strip() for k in (paper.keywords or '').split(',') if k.strip()]
        if keywords_list:
            top_kw = " ".join(keywords_list[:4])
            area_display = paper.get_research_area_display() if paper.research_area else ""
            concept_query = f"{top_kw} {area_display}".strip()
            if concept_query and concept_query not in queries:
                queries.append(concept_query)

        # 3. Core title nouns/keywords query (removes common stopwords)
        stopwords = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'were', 'will', 'with', 'using', 'based', 'via',
            'study', 'approach', 'novel', 'new', 'towards', 'toward'
        }
        words = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', clean_title.lower()) if w not in stopwords]
        if words:
            concise_query = " ".join(words[:6])
            if concise_query and concise_query not in queries:
                queries.append(concise_query)

        return queries or [clean_title or "artificial intelligence research"]

    def search_google_scholar(
        self,
        query: str,
        limit: int = 5,
        as_ylo: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search Google Scholar through SerpApi or resilient scholarly fallback.
        Handles timeouts, HTTP errors, rate limits, and network errors gracefully.
        Never throws uncaught exceptions that could disrupt main workflows.
        """
        if not query or not query.strip():
            return []

        limit = min(limit or self.max_results, 10)

        if self.is_configured:
            try:
                params = {
                    'engine': 'google_scholar',
                    'q': query.strip(),
                    'api_key': self.api_key.strip(),
                    'num': limit,
                }
                if as_ylo:
                    params['as_ylo'] = as_ylo

                response = requests.get(
                    'https://serpapi.com/search.json',
                    params=params,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    data = response.json()
                    organic_results = data.get('organic_results', [])
                    return organic_results[:limit]
                elif response.status_code == 429:
                    logger.warning("Google Scholar API provider rate limit reached (HTTP 429). Falling back gracefully.")
                    return self._fallback_scholarly_search(query, limit=limit, as_ylo=as_ylo)
                elif response.status_code in (401, 403):
                    logger.warning(f"Google Scholar API provider authentication failed (HTTP {response.status_code}).")
                    return self._fallback_scholarly_search(query, limit=limit, as_ylo=as_ylo)
                else:
                    logger.warning(f"Google Scholar API provider returned HTTP {response.status_code}: {response.text[:200]}")
                    return self._fallback_scholarly_search(query, limit=limit, as_ylo=as_ylo)

            except requests.exceptions.Timeout:
                logger.warning(f"Google Scholar API request timed out after {self.timeout}s for query: '{query[:50]}'")
                return self._fallback_scholarly_search(query, limit=limit, as_ylo=as_ylo)
            except requests.exceptions.RequestException as e:
                logger.warning(f"Google Scholar API network error: {e}")
                return self._fallback_scholarly_search(query, limit=limit, as_ylo=as_ylo)
            except Exception as e:
                logger.error(f"Unexpected error querying Google Scholar API: {e}")
                return self._fallback_scholarly_search(query, limit=limit, as_ylo=as_ylo)
        else:
            # When SERPAPI_API_KEY is not configured, use scholarly open API fallback
            return self._fallback_scholarly_search(query, limit=limit, as_ylo=as_ylo)

    def _fallback_scholarly_search(
        self,
        query: str,
        limit: int = 5,
        as_ylo: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Resilient open scholarly fallback (Semantic Scholar / CrossRef) when SerpApi
        is unconfigured, offline, or rate-limited.
        """
        try:
            headers = {'User-Agent': 'ScholarLensResearchBot/2.0 (mailto:admin@scholarlens.local)'}
            url = 'https://api.semanticscholar.org/graph/v1/paper/search'
            params = {
                'query': query[:120],
                'limit': limit,
                'fields': 'title,abstract,authors,year,url,citationCount,externalIds'
            }
            if as_ylo:
                params['year'] = f"{as_ylo}-"

            resp = requests.get(url, params=params, headers=headers, timeout=min(self.timeout, 5))
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for p in data.get('data', []):
                    authors_list = [a.get('name', '') for a in p.get('authors', []) if a.get('name')]
                    ext_ids = p.get('externalIds') or {}
                    ext_id = ext_ids.get('DOI') or ext_ids.get('ArXiv') or p.get('paperId') or ''
                    results.append({
                        'title': p.get('title', ''),
                        'link': p.get('url') or (f"https://doi.org/{ext_ids.get('DOI')}" if ext_ids.get('DOI') else ''),
                        'snippet': p.get('abstract') or '',
                        'result_id': ext_id,
                        'publication_info': {
                            'summary': f"{', '.join(authors_list[:3])} - {p.get('year', '')}",
                            'authors': [{'name': a} for a in authors_list]
                        },
                        'inline_links': {
                            'cited_by': {'total': p.get('citationCount', 0)}
                        },
                        'year': p.get('year')
                    })
                return results[:limit]
        except Exception as e:
            logger.debug(f"Open scholarly fallback search error (non-fatal): {e}")

        return []

    def normalize_result(self, raw_item: Dict[str, Any], source_name: str = 'GOOGLE_SCHOLAR') -> Dict[str, Any]:
        """
        Normalize raw API result into standardized Scholar_Lens research paper metadata.
        Safely handles missing titles, authors, DOIs, snippets, and publication dates.
        """
        # Clean title
        raw_title = raw_item.get('title') or ''
        title = re.sub(r'\[(PDF|HTML|BOOK|CITATION|DOC)\]\s*', '', raw_title, flags=re.IGNORECASE).strip()
        if not title:
            title = "Untitled Research Paper"

        # Link / External URL
        link = raw_item.get('link') or raw_item.get('url') or ''

        # Abstract / Snippet
        snippet = raw_item.get('snippet') or raw_item.get('abstract') or ''
        # Clean trailing ellipses
        snippet = re.sub(r'[\r\n\t]+', ' ', snippet).strip()

        # Authors & Year from publication_info
        pub_info = raw_item.get('publication_info') or {}
        summary_str = pub_info.get('summary') or ''
        
        authors = []
        if 'authors' in pub_info and isinstance(pub_info['authors'], list):
            for a in pub_info['authors']:
                name = a.get('name') if isinstance(a, dict) else str(a)
                if name and name.strip():
                    authors.append(name.strip())
        elif summary_str:
            parts = summary_str.split(' - ')
            if parts:
                author_names = parts[0].split(',')
                for an in author_names:
                    an_clean = an.strip()
                    if an_clean and len(an_clean) < 60:
                        authors.append(an_clean)

        # Extract publication year (recency preservation)
        pub_date = None
        year = raw_item.get('year')
        if not year and summary_str:
            year_match = re.search(r'\b(19\d\d|20[0-2]\d)\b', summary_str)
            if year_match:
                year = int(year_match.group(1))

        if year:
            try:
                year_int = int(year)
                # Valid academic publication year boundary
                if 1900 <= year_int <= timezone.now().year + 1:
                    pub_date = datetime.date(year_int, 1, 1)
            except (ValueError, TypeError):
                pub_date = None

        # Citations
        citations = 0
        inline_links = raw_item.get('inline_links') or {}
        cited_by = inline_links.get('cited_by') or {}
        if isinstance(cited_by, dict):
            citations = cited_by.get('total', 0)
        elif raw_item.get('citationCount'):
            citations = raw_item.get('citationCount', 0)

        try:
            citations = int(citations or 0)
        except (ValueError, TypeError):
            citations = 0

        # Unique external ID for deduplication
        external_id = str(raw_item.get('result_id') or raw_item.get('cluster_id') or '')
        if not external_id and link:
            external_id = hashlib.sha256(link.encode('utf-8')).hexdigest()[:32]
        elif not external_id and title:
            external_id = hashlib.sha256(title.lower().encode('utf-8')).hexdigest()[:32]

        return {
            'title': title,
            'abstract': snippet or f"Abstract excerpt for {title}.",
            'authors': authors or ['Academic Contributor'],
            'external_url': link,
            'external_id': external_id,
            'publication_date': pub_date,
            'citation_count': max(0, citations),
            'source': source_name,
            'is_external': True,
        }

    def deduplicate_and_store(
        self,
        normalized_items: List[Dict[str, Any]],
        research_area: str = 'OTHER',
        auto_index: bool = True
    ) -> List[ResearchPaper]:
        """
        Idempotently store normalized papers into ResearchPaper table.
        Avoids creating duplicate records when run repeatedly.
        Distinguishes external papers with is_external=True and source='GOOGLE_SCHOLAR'.
        """
        stored_papers = []

        for item in normalized_items:
            title = item.get('title', '').strip()
            if not title or title.lower() == "untitled research paper":
                continue

            external_id = item.get('external_id', '').strip()
            external_url = item.get('external_url', '').strip()
            pub_date = item.get('publication_date')
            citations = item.get('citation_count', 0)

            # Deduplication strategy:
            # 1. Match by non-empty external_id and source
            # 2. Match by non-empty external_url
            # 3. Match by normalized exact title
            existing_paper = None

            if external_id:
                existing_paper = ResearchPaper.objects.filter(external_id=external_id).first()

            if not existing_paper and external_url:
                existing_paper = ResearchPaper.objects.filter(external_url=external_url).first()

            if not existing_paper:
                existing_paper = ResearchPaper.objects.filter(title__iexact=title).first()

            if existing_paper:
                # Update metadata if newly available without corrupting existing fields
                updated = False
                if pub_date and not existing_paper.publication_date:
                    existing_paper.publication_date = pub_date
                    updated = True
                if external_url and not existing_paper.external_url:
                    existing_paper.external_url = external_url
                    updated = True
                if external_id and not existing_paper.external_id:
                    existing_paper.external_id = external_id
                    updated = True
                if citations and (existing_paper.citation_count or 0) < citations:
                    existing_paper.citation_count = citations
                    updated = True
                if updated:
                    existing_paper.save()
                stored_papers.append(existing_paper)
                continue

            # Create new external paper
            try:
                with transaction.atomic():
                    paper = ResearchPaper.objects.create(
                        uploader=None,
                        title=title,
                        abstract=item.get('abstract') or f"Academic paper on {title}.",
                        research_area=research_area or ResearchPaper.ResearchArea.OTHER,
                        keywords=re.sub(r'[^a-zA-Z0-9, ]', '', title[:120]),
                        status=ResearchPaper.PaperStatus.TEXT_EXTRACTED,
                        pdf_file=None,
                        extracted_text=item.get('abstract', ''),
                        page_count=1,
                        word_count=len((item.get('abstract') or '').split()),
                        source=item.get('source', 'GOOGLE_SCHOLAR'),
                        external_id=external_id,
                        external_url=external_url,
                        publication_date=pub_date,
                        citation_count=citations,
                        is_external=True
                    )

                    # Create author records
                    for idx, author_name in enumerate(item.get('authors', [])):
                        PaperAuthor.objects.create(
                            paper=paper,
                            name=author_name[:255],
                            order=idx + 1,
                            is_corresponding=(idx == 0)
                        )

                    # Auto-index chunks for vector/lexical retrieval
                    if auto_index and item.get('abstract'):
                        chunk_text = item.get('abstract')
                        chunk = PaperChunk.objects.create(
                            paper=paper,
                            chunk_index=0,
                            page_number=1,
                            section='Abstract',
                            start_offset=0,
                            end_offset=len(chunk_text),
                            content=chunk_text,
                            token_count=len(chunk_text.split())
                        )
                        # Optionally generate embedding if AI configured
                        try:
                            from ai_engine.services import AIService
                            ai = AIService()
                            if ai.is_configured:
                                from papers.models import PaperEmbedding
                                emb = ai.generate_embedding(chunk_text)
                                PaperEmbedding.objects.create(
                                    chunk=chunk,
                                    embedding=emb,
                                    model_name=ai.embedding_model
                                )
                        except Exception:
                            pass

                    stored_papers.append(paper)

            except Exception as e:
                logger.error(f"Error storing external paper '{title[:40]}': {e}")
                continue

        return stored_papers

    def search_and_retrieve_similar(self, paper: ResearchPaper, limit: int = 5) -> List[ResearchPaper]:
        """
        High-level pipeline:
        1. Formulates queries from uploaded paper.
        2. Queries Google Scholar provider.
        3. Normalizes and deduplicates results.
        4. Returns stored ResearchPaper records ready for comparison.
        """
        queries = self.generate_search_queries(paper)
        raw_results = []
        seen_titles = set()

        for q in queries:
            if len(raw_results) >= limit:
                break
            results = self.search_google_scholar(q, limit=limit)
            for r in results:
                t = (r.get('title') or '').strip().lower()
                if t and t not in seen_titles and t != paper.title.strip().lower():
                    seen_titles.add(t)
                    raw_results.append(r)
                if len(raw_results) >= limit:
                    break

        normalized = [self.normalize_result(r, source_name='GOOGLE_SCHOLAR') for r in raw_results]
        return self.deduplicate_and_store(
            normalized,
            research_area=paper.research_area or 'OTHER',
            auto_index=True
        )

    def sync_latest_research(self, areas: Optional[List[str]] = None, limit_per_area: int = 3) -> Dict[str, Any]:
        """
        Periodic synchronizer:
        Queries latest scholarly developments, emerging technologies, and research trends.
        Safe to run repeatedly (100% idempotent).
        """
        current_year = timezone.now().year
        default_disciplines = [
            ('AI_ML', 'Artificial Intelligence foundation models transformer architecture'),
            ('NLP', 'Large language models reasoning emergent capabilities NLP'),
            ('COMPUTER_VISION', 'Diffusion models vision transformers multimodal representation'),
            ('CYBERSECURITY', 'Zero trust architecture cryptographic protocols AI security'),
            ('QUANTUM_COMPUTING', 'Quantum error correction fault tolerant quantum algorithms'),
        ]

        total_synced = 0
        newly_added = 0
        synced_papers = []

        for area_code, search_phrase in default_disciplines:
            if areas and area_code not in areas:
                continue

            raw_results = self.search_google_scholar(
                search_phrase,
                limit=limit_per_area,
                as_ylo=current_year - 1
            )
            normalized = [self.normalize_result(r, source_name='GOOGLE_SCHOLAR') for r in raw_results]
            
            before_count = ResearchPaper.objects.filter(is_external=True).count()
            stored = self.deduplicate_and_store(normalized, research_area=area_code, auto_index=True)
            after_count = ResearchPaper.objects.filter(is_external=True).count()

            newly_added += max(0, after_count - before_count)
            total_synced += len(stored)
            synced_papers.extend(stored)

        return {
            'success': True,
            'total_synced': total_synced,
            'newly_added': newly_added,
            'papers': synced_papers,
            'timestamp': timezone.now().isoformat()
        }
