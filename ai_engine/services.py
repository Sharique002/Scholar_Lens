import os, json, logging, hashlib
import numpy as np
from django.conf import settings
from ai_engine.models import AIAnalysis, ResearchGap, ChatMessage

logger = logging.getLogger('scholar_lens')

class AIServiceError(Exception): pass
class AIServiceNotConfigured(AIServiceError): pass

def cosine_similarity(vec_a, vec_b) -> float:
    a = np.array(vec_a)
    b = np.array(vec_b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

class AIService:
    """Abstraction layer for AI API calls."""
    def __init__(self):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
        self.embedding_model = getattr(settings, 'OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        self._client = None
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def _get_client(self):
        if not self.is_configured:
            raise AIServiceNotConfigured('OpenAI API key not configured. Set OPENAI_API_KEY in your environment.')
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client
    
    def chat_completion(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> dict:
        """Make a chat completion request."""
        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                temperature=temperature,
                response_format={'type': 'json_object'},
            )
            content = response.choices[0].message.content
            tokens = response.usage.total_tokens if response.usage else 0
            return {'content': json.loads(content), 'tokens_used': tokens, 'model': self.model}
        except Exception as e:
            logger.error(f'AI Service error: {e}')
            raise AIServiceError(f'AI service request failed: {str(e)}')
    
    def generate_embedding(self, text: str) -> list:
        """Generate embedding vector for text."""
        client = self._get_client()
        try:
            text = text[:8000]  # Truncate to stay within limits
            response = client.embeddings.create(model=self.embedding_model, input=text)
            return response.data[0].embedding
        except Exception as e:
            logger.error(f'Embedding error: {e}')
            raise AIServiceError(f'Embedding generation failed: {str(e)}')

SECTION_PATTERNS = [
    (r'(?i)^\s*(?:[0-9]+\.?\s*)?(abstract)\b', 'Abstract'),
    (r'(?i)^\s*(?:[0-9]+\.?\s*)?(introduction|overview)\b', 'Introduction'),
    (r'(?i)^\s*(?:[0-9]+\.?\s*)?(related\s+work|literature\s+review|background)\b', 'Related Work'),
    (r'(?i)^\s*(?:[0-9]+\.?\s*)?(methodology|methods|system\s+design|architecture|approach|formulation)\b', 'Methodology'),
    (r'(?i)^\s*(?:[0-9]+\.?\s*)?(experiments|experimental\s+setup|evaluation|implementation)\b', 'Experiments'),
    (r'(?i)^\s*(?:[0-9]+\.?\s*)?(results|findings)\b', 'Results'),
    (r'(?i)^\s*(?:[0-9]+\.?\s*)?(discussion|analysis)\b', 'Discussion'),
    (r'(?i)^\s*(?:[0-9]+\.?\s*)?(conclusion|concluding\s+remarks|future\s+work)\b', 'Conclusion'),
    (r'(?i)^\s*(?:[0-9]+\.?\s*)?(references|bibliography)\b', 'References'),
]

class PaperProcessor:
    """Handles robust PDF text extraction, section detection, and page-mapped chunking."""

    def _detect_section(self, text_snippet: str, current_section: str = 'Body') -> str:
        import re
        lines = text_snippet.split('\n')[:15]
        for line in lines:
            line_str = line.strip()
            if not line_str or len(line_str) > 60:
                continue
            for pattern, sec_name in SECTION_PATTERNS:
                if re.match(pattern, line_str):
                    return sec_name
        return current_section

    def _identify_sections(self, text: str) -> list:
        import re
        detected = []
        for line in text.split('\n'):
            line_str = line.strip()
            if not line_str or len(line_str) > 60:
                continue
            for pattern, sec_name in SECTION_PATTERNS:
                if re.match(pattern, line_str):
                    if not detected or detected[-1][0] != sec_name:
                        detected.append((sec_name, line_str))
        return detected

    def extract_text_from_bytes(self, pdf_bytes: bytes) -> dict:
        try:
            try:
                import pymupdf as fitz
            except ImportError:
                import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            if doc.is_encrypted and not doc.authenticate(''):
                return {'success': False, 'error': 'PDF is password encrypted', 'page_count': 0, 'text': ''}
            full_text_list = []
            for page in doc:
                text = page.get_text() or ''
                full_text_list.append(text.replace('\x00', ' '))
            full_text = "\n\n".join(full_text_list).strip()
            return {
                'success': True,
                'page_count': len(doc),
                'text': full_text,
                'is_scanned': len(full_text) < 30 and len(doc) > 0
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'page_count': 0, 'text': ''}

    def extract_text(self, paper) -> str:
        if not paper.pdf_file:
            raise AIServiceError("No PDF file attached to paper.")

        pdf_path = paper.pdf_file.path
        if not os.path.exists(pdf_path):
            paper.status = 'FAILED'
            paper.save()
            raise AIServiceError(f"PDF file does not exist at {pdf_path}")

        max_upload = getattr(settings, 'MAX_UPLOAD_SIZE', 20 * 1024 * 1024)
        if os.path.getsize(pdf_path) > max_upload:
            paper.status = 'FAILED'
            paper.save()
            raise AIServiceError(f"PDF exceeds maximum allowed file size of {max_upload // (1024 * 1024)}MB.")

        try:
            try:
                import pymupdf as fitz
            except ImportError:
                import fitz

            doc = fitz.open(pdf_path)
            if doc.is_encrypted and not doc.authenticate(''):
                raise AIServiceError("PDF is password-encrypted and cannot be processed.")

            page_records = []
            full_text_list = []
            current_sec = 'Introduction'

            for page in doc:
                page_text = page.get_text() or ''
                # Clean invalid null bytes
                page_text = page_text.replace('\x00', ' ')
                page_num = page.number + 1
                current_sec = self._detect_section(page_text, current_sec)
                page_records.append({
                    'page_number': page_num,
                    'section': current_sec,
                    'text': page_text,
                })
                full_text_list.append(page_text)

            full_text = "\n\n".join(full_text_list).strip()
            if len(full_text) < 30 and len(doc) > 0:
                logger.warning(f"Paper '{paper.title}' contains minimal extractable text (<30 chars). Scanned PDF detected.")

            paper.extracted_text = full_text
            paper.page_count = len(doc)
            paper.word_count = len(full_text.split())
            paper.status = 'TEXT_EXTRACTED'
            paper.save()
            return full_text
        except AIServiceError:
            paper.status = 'FAILED'
            paper.save()
            raise
        except Exception as e:
            paper.status = 'FAILED'
            paper.save()
            logger.error(f"Failed to extract text from {paper.title}: {e}")
            raise AIServiceError(f"Extraction failed: {e}")

    def chunk_text(self, text: str, chunk_size=800, overlap=150) -> list[str]:
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            i += max(1, chunk_size - overlap)
        return chunks

    def process_paper(self, paper):
        """Full pipeline: extraction, section mapping, chunking, and embedding."""
        try:
            full_text = self.extract_text(paper)
            from papers.models import PaperChunk, PaperEmbedding
            ai = AIService()

            try:
                import pymupdf as fitz
                doc = fitz.open(paper.pdf_file.path)
            except Exception:
                doc = None

            PaperChunk.objects.filter(paper=paper).delete()
            chunk_idx = 0
            running_offset = 0

            if doc and len(doc) > 0:
                current_sec = 'Introduction'
                for page in doc:
                    p_text = (page.get_text() or '').replace('\x00', ' ').strip()
                    if not p_text:
                        continue
                    p_num = page.number + 1
                    current_sec = self._detect_section(p_text, current_sec)
                    page_chunks = self.chunk_text(p_text, chunk_size=500, overlap=100)
                    for c_text in page_chunks:
                        start_pos = running_offset + p_text.find(c_text[:50]) if p_text.find(c_text[:50]) >= 0 else running_offset
                        end_pos = start_pos + len(c_text)
                        chunk = PaperChunk.objects.create(
                            paper=paper,
                            chunk_index=chunk_idx,
                            page_number=p_num,
                            section=current_sec,
                            start_offset=max(0, start_pos),
                            end_offset=max(0, end_pos),
                            content=c_text,
                            token_count=len(c_text.split())
                        )
                        if ai.is_configured:
                            try:
                                emb = ai.generate_embedding(c_text)
                                PaperEmbedding.objects.create(
                                    chunk=chunk,
                                    embedding=emb,
                                    model_name=ai.embedding_model
                                )
                            except Exception as emb_err:
                                logger.warning(f"Embedding generation skipped for chunk {chunk.id}: {emb_err}")
                        chunk_idx += 1
                    running_offset += len(p_text) + 2
            else:
                # Fallback text chunking
                chunks = self.chunk_text(full_text)
                for idx, chunk_text in enumerate(chunks):
                    chunk = PaperChunk.objects.create(
                        paper=paper,
                        chunk_index=idx,
                        page_number=1,
                        section='Abstract' if idx == 0 else 'Body',
                        start_offset=idx * 500,
                        end_offset=(idx + 1) * 500,
                        content=chunk_text,
                        token_count=len(chunk_text.split())
                    )
                    if ai.is_configured:
                        try:
                            emb = ai.generate_embedding(chunk_text)
                            PaperEmbedding.objects.create(chunk=chunk, embedding=emb, model_name=ai.embedding_model)
                        except Exception:
                            pass

            paper.status = 'INDEXED'
            paper.save()
        except Exception as e:
            paper.status = 'FAILED'
            paper.save()
            logger.error(f"Paper processing failed: {e}")
            raise

class PaperSummarizer:
    def summarize(self, paper) -> dict:
        existing = AIAnalysis.objects.filter(paper=paper, analysis_type='SUMMARY').first()
        if existing:
            return existing.result
        
        if not paper.extracted_text and paper.pdf_file:
            try:
                PaperProcessor().extract_text(paper)
            except Exception as e:
                logger.warning(f"Could not extract text before summary: {e}")

        ai = AIService()
        system_prompt = "You are an expert research assistant. Provide a structured summary of the given academic paper in JSON format with keys: 'summary', 'research_problem', 'methodology', 'datasets', 'key_findings', 'limitations', 'future_work', 'keywords' (list of strings)."
        content_text = paper.extracted_text[:100000] if paper.extracted_text else (paper.abstract or paper.title)
        user_prompt = f"Analyze the following paper text and summarize it:\n\n{content_text}"
        
        response = ai.chat_completion(system_prompt, user_prompt)
        result = response['content']
        
        AIAnalysis.objects.create(
            paper=paper,
            analysis_type='SUMMARY',
            result=result,
            prompt_used=user_prompt[:1000],
            model_name=response['model'],
            tokens_used=response['tokens_used']
        )
        return result

class ResearchGapDetector:
    def detect_gaps(self, paper) -> list:
        from ai_engine.models import ResearchGap
        existing_gaps = ResearchGap.objects.filter(paper=paper)
        if existing_gaps.exists():
            return list(existing_gaps)
        
        if not paper.extracted_text and paper.pdf_file:
            try:
                PaperProcessor().extract_text(paper)
            except Exception as e:
                logger.warning(f"Could not extract text before gap detection: {e}")

        ai = AIService()
        system_prompt = "You are an expert researcher. Identify research gaps in the given paper. Return JSON with key 'gaps' containing a list of dictionaries with keys: 'title', 'description', 'area', 'severity' (HIGH, MEDIUM, or LOW), and 'suggestions'."
        content_text = paper.extracted_text[:100000] if paper.extracted_text else (paper.abstract or paper.title)
        user_prompt = f"Analyze the following paper text and identify research gaps:\n\n{content_text}"
        
        response = ai.chat_completion(system_prompt, user_prompt)
        result = response['content']
        
        gaps_to_return = []
        for gap_data in result.get('gaps', []):
            gap = ResearchGap.objects.create(
                paper=paper,
                title=gap_data.get('title', 'Unknown Title'),
                description=gap_data.get('description', ''),
                area=gap_data.get('area', 'General'),
                severity=gap_data.get('severity', 'LOW'),
                suggestions=gap_data.get('suggestions', '')
            )
            gaps_to_return.append(gap)
            
        return gaps_to_return

class ResearchQuestionAnswerer:
    """Source-aware, grounded RAG Q&A engine with verifiable section and page citations."""

    FALLBACK_NO_EVIDENCE = "The available paper content does not provide enough evidence to answer this question confidently."

    def answer_question(self, paper, question, user=None) -> dict:
        ai = AIService()
        from papers.models import PaperChunk, PaperEmbedding

        if user is None:
            user = getattr(paper, 'uploader', None)

        if not PaperChunk.objects.filter(paper=paper).exists() and paper.pdf_file:
            try:
                PaperProcessor().process_paper(paper)
            except Exception as e:
                logger.warning(f"Could not auto-process paper chunks for RAG: {e}")

        all_chunks = list(PaperChunk.objects.filter(paper=paper).order_by('chunk_index'))
        if not all_chunks:
            if not paper.abstract:
                msg = "The available paper content does not provide enough evidence to answer this question confidently."
                ChatMessage.objects.create(paper=paper, user=user, question=question, answer=msg, sources=[])
                return {'answer': msg, 'sources': []}

        # Vector retrieval or lexical keyword scoring
        top_chunks = []
        q_words = set(w.lower() for w in question.split() if len(w) > 2)

        if ai.is_configured:
            try:
                q_emb = ai.generate_embedding(question)
                embeddings = PaperEmbedding.objects.filter(chunk__paper=paper).select_related('chunk')
                if embeddings.exists():
                    scored = [(cosine_similarity(q_emb, pe.embedding), pe.chunk) for pe in embeddings]
                    scored.sort(key=lambda x: x[0], reverse=True)
                    top_chunks = [chunk for sim, chunk in scored[:4] if sim > 0.35]
            except Exception as e:
                logger.warning(f"Vector search failed in RAG, using lexical chunk ranking: {e}")

        if not top_chunks and all_chunks:
            # Lexical chunk scoring
            scored_chunks = []
            for c in all_chunks:
                c_words = set(c.content.lower().split())
                overlap = len(q_words.intersection(c_words))
                scored_chunks.append((overlap, c))
            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            if scored_chunks and scored_chunks[0][0] > 0:
                top_chunks = [c for score, c in scored_chunks[:3] if score > 0]
            else:
                top_chunks = all_chunks[:2]

        # Check if question has any evidence in document
        has_evidence = bool(top_chunks)
        if not has_evidence:
            msg = "The available paper content does not provide enough evidence to answer this question confidently."
            ChatMessage.objects.create(paper=paper, user=user, question=question, answer=msg, sources=[])
            return {'answer': msg, 'sources': []}

        # Build structured sources
        structured_sources = []
        context_parts = []
        for idx, c in enumerate(top_chunks):
            src_num = idx + 1
            sec = c.section or "Document Context"
            page = c.page_number or 1
            snippet = c.content[:240].strip() + ("..." if len(c.content) > 240 else "")
            structured_sources.append({
                'source_id': src_num,
                'chunk_id': c.id,
                'section': sec,
                'page_number': page,
                'snippet': snippet,
            })
            context_parts.append(f"[{src_num}] {sec} (Page {page}):\n{c.content}")

        context_str = "\n\n".join(context_parts)

        # Generate answer with AI or structured grounded fallback
        if ai.is_configured:
            try:
                system_prompt = (
                    "You are a strict, evidence-grounded academic research assistant. "
                    "Answer the user's question using ONLY the provided paper sources. "
                    "In your answer, cite your sources using bracketed notation like [1], [2] "
                    "corresponding to the numbered sources provided. "
                    "If the sources do not contain enough information to answer the question, state: "
                    "'The available paper content does not provide enough evidence to answer this question confidently.' "
                    "Return JSON with keys: 'answer' (string) and 'sources' (list of cited source_id numbers)."
                )
                user_prompt = f"Paper Title: {paper.title}\n\nContext Sources:\n{context_str}\n\nQuestion: {question}"
                response = ai.chat_completion(system_prompt, user_prompt)
                res_content = response.get('content', {})
                answer_text = res_content.get('answer', '')
                cited_ids = res_content.get('sources', [s['source_id'] for s in structured_sources])
                final_sources = [s for s in structured_sources if s['source_id'] in cited_ids] or structured_sources
            except Exception as e:
                logger.warning(f"AI chat completion failed in RAG, using grounded extractive synthesis: {e}")
                answer_text = None
        else:
            answer_text = None

        if not answer_text:
            # Grounded Extractive Synthesis Fallback
            primary = structured_sources[0]
            answer_text = (
                f"Based on {primary['section']} (Page {primary['page_number']}):\n\n"
                f"{primary['snippet']}\n\n"
                f"Reference: [{primary['source_id']}] {primary['section']} — Page {primary['page_number']}."
            )
            final_sources = [primary]

        ChatMessage.objects.create(
            paper=paper,
            user=user,
            question=question,
            answer=answer_text,
            sources=final_sources
        )

        return {'answer': answer_text, 'sources': final_sources}

class SemanticSearchService:
    def search(self, query: str, research_area: str = None, limit: int = 20) -> list:
        """Search papers semantically using vector embeddings, or fall back to keyword relevance."""
        ai = AIService()
        if not ai.is_configured:
            from papers.models import ResearchPaper
            from django.db.models import Q
            qs = ResearchPaper.objects.all()
            if research_area:
                qs = qs.filter(research_area=research_area)
            words = [w.lower() for w in query.split() if len(w) > 2]
            results = []
            for paper in qs:
                text = f"{paper.title} {paper.abstract} {paper.keywords}".lower()
                matches = sum(1 for w in words if w in text)
                if matches > 0:
                    score = min(95.0, round((matches / max(len(words), 1)) * 100, 1))
                    results.append({'paper': paper, 'score': score, 'score_raw': score / 100.0})
            results.sort(key=lambda x: x['score_raw'], reverse=True)
            return [{'paper': item['paper'], 'score': item['score']} for item in results[:limit]]

        query_embedding = ai.generate_embedding(query)
        
        from papers.models import PaperEmbedding
        qs = PaperEmbedding.objects.select_related('chunk', 'chunk__paper')
        if research_area:
            qs = qs.filter(chunk__paper__research_area=research_area)

        # Aggregate highest similarity score per paper
        paper_max_scores = {}
        for pe in qs:
            paper = pe.chunk.paper
            sim = cosine_similarity(query_embedding, pe.embedding)
            if sim > 0.4:  # reasonable semantic relevance threshold
                if paper.id not in paper_max_scores or sim > paper_max_scores[paper.id]['score_raw']:
                    paper_max_scores[paper.id] = {
                        'paper': paper,
                        'score': round(sim * 100, 1),
                        'score_raw': sim
                    }

        ranked_results = sorted(paper_max_scores.values(), key=lambda x: x['score_raw'], reverse=True)
        # Return format expected by views and templates: [{'paper': paper, 'score': score}]
        return [{'paper': item['paper'], 'score': item['score']} for item in ranked_results[:limit]]

def semantic_search(query: str, research_area: str = None, limit: int = 20) -> list:
    """Convenience functional wrapper for semantic search."""
    service = SemanticSearchService()
    return service.search(query=query, research_area=research_area, limit=limit)

