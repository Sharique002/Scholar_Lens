"""
Scholar Lens Advanced Hardening & Edge-Case Test Suite.
Tests canonical 7-dimension evaluation, provenance tracking, source-aware RAG,
PDF processing edge cases, hybrid search ranking, explainable recommendations,
and security boundaries.
"""
import uuid
import json
from datetime import date
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone

from accounts.models import UserProfile
from researchers.models import ResearcherProfile, ResearchInterest, Skill
from papers.models import ResearchPaper, PaperChunk
from projects.models import ResearchProject, ProjectMember
from collaboration.models import CollaborationRequest
from ai_engine.models import AIAnalysis, ResearchGap, ChatMessage
from ai_engine.services import PaperProcessor, ResearchQuestionAnswerer
from evaluation.models import EvaluationReport, ResearchScore
from evaluation.services import ResearchEvaluator, SimilarityAnalyzer
from search.services import HybridSearchEngine
from dashboard.models import ResearchActivity


class AdvancedHardeningTestBase(TestCase):
    """Base setup for advanced hardening tests."""

    def setUp(self):
        self.user_a = User.objects.create_user(
            username='alice_res', password='Password123!', email='alice@example.com'
        )
        self.profile_a, _ = UserProfile.objects.get_or_create(
            user=self.user_a, defaults={'role': 'FACULTY', 'institution': 'MIT'}
        )
        self.researcher_a, _ = ResearcherProfile.objects.get_or_create(
            user=self.user_a, defaults={'headline': 'Dr. Alice, Computer Science', 'expertise_summary': 'AI and Deep Learning'}
        )

        self.user_b = User.objects.create_user(
            username='bob_res', password='Password123!', email='bob@example.com'
        )
        self.profile_b, _ = UserProfile.objects.get_or_create(
            user=self.user_b, defaults={'role': 'STUDENT', 'institution': 'Stanford'}
        )
        self.researcher_b, _ = ResearcherProfile.objects.get_or_create(
            user=self.user_b, defaults={'headline': 'Bob, Data Science', 'expertise_summary': 'Data Science and Cloud Systems'}
        )

        self.paper_a = ResearchPaper.objects.create(
            title='Attention Is All You Need In Neural Architecture',
            abstract='Transformer models rely on self-attention mechanisms to compute representations.',
            research_area='AI_ML',
            keywords='attention, transformer, neural network',
            status='PROCESSED',
            uploader=self.user_a,
        )

        self.paper_b = ResearchPaper.objects.create(
            title='Quantum Key Distribution via Entangled Photons',
            abstract='Experimental verification of quantum cryptography protocols under noise.',
            research_area='QUANTUM',
            keywords='quantum, cryptography, photons',
            status='PROCESSED',
            uploader=self.user_b,
        )


# =============================================================================
# 1. Canonical 7-Dimension Evaluation & Weights Tests
# =============================================================================

class Canonical7DimensionEvaluationTest(AdvancedHardeningTestBase):
    """Verify canonical 7 dimensions, weights summing to 100%, and structured scoring."""

    def test_settings_evaluation_weights_sum_to_100(self):
        """Weights must be exactly 100% and have all 7 canonical keys."""
        weights = getattr(settings, 'EVALUATION_WEIGHTS', {})
        expected_keys = {
            'novelty', 'research_gap', 'methodology', 'contribution',
            'evidence_quality', 'technical_strength', 'clarity'
        }
        self.assertEqual(set(weights.keys()), expected_keys)
        total_weight = sum(weights.values())
        self.assertEqual(total_weight, 100, f"Weights sum to {total_weight}, expected 100")
        self.assertEqual(weights['novelty'], 20)
        self.assertEqual(weights['research_gap'], 15)
        self.assertEqual(weights['methodology'], 15)
        self.assertEqual(weights['contribution'], 15)
        self.assertEqual(weights['evidence_quality'], 15)
        self.assertEqual(weights['technical_strength'], 10)
        self.assertEqual(weights['clarity'], 10)

    def test_evaluator_analytical_scoring_produces_7_canonical_dimensions(self):
        """Evaluating paper analytically produces all 7 dimensions with evidence."""
        evaluator = ResearchEvaluator()
        result = evaluator.evaluate_paper(self.paper_a)

        self.assertTrue(result['success'])
        self.assertIn('evaluation_id', result)
        self.assertIn('overall_score', result)
        self.assertIn('confidence', result)
        self.assertIn('limitations', result)

        scores = result['scores']
        self.assertEqual(len(scores), 7)
        dimension_names = {s['dimension'] for s in scores}
        expected_dims = {
            'NOVELTY', 'RESEARCH_GAP', 'METHODOLOGY', 'CONTRIBUTION',
            'EVIDENCE_QUALITY', 'TECHNICAL_STRENGTH', 'CLARITY'
        }
        self.assertEqual(dimension_names, expected_dims)

        for s in scores:
            self.assertIn('score', s)
            self.assertIn('weight', s)
            self.assertIn('assessment', s)
            self.assertIn('evidence', s)
            self.assertIn('confidence', s)
            self.assertIn('limitations', s)
            # Evidence must be structured
            self.assertIsInstance(s['evidence'], list)
            if s['evidence']:
                ev = s['evidence'][0]
                self.assertIn('section', ev)
                self.assertIn('page', ev)
                self.assertIn('snippet', ev)

    def test_evaluation_report_properties_and_backward_compatibility(self):
        """Test model properties for canonical 7 dimensions and backwards compatibility."""
        report = EvaluationReport.objects.create(
            paper=self.paper_a,
            overall_score=82.5,
            provider='ScholarLens Analytical Engine',
            model_version='v2.0-deterministic',
            prompt_version='2026.1-canonical',
            scoring_framework_version='7-dim-v1.0',
            confidence=0.88,
            limitations='Analytical heuristic evaluation based on paper text.',
        )

        dims = [
            ('NOVELTY', 85.0, 20),
            ('RESEARCH_GAP', 78.0, 15),
            ('METHODOLOGY', 82.0, 15),
            ('CONTRIBUTION', 80.0, 15),
            ('EVIDENCE_QUALITY', 84.0, 15),
            ('TECHNICAL_STRENGTH', 88.0, 10),
            ('CLARITY', 90.0, 10),
        ]
        for dim, sc, wt in dims:
            ResearchScore.objects.create(
                report=report,
                dimension=dim,
                score=sc,
                weight=wt,
                explanation=f'{dim} assessment',
                supporting_evidence=[{'section': 'Abstract', 'page': 1, 'snippet': 'Evidence snippet'}],
                confidence='High',
                limitations='Preliminary estimate.',
            )

        # Canonical properties
        self.assertEqual(report.novelty_score, 85.0)
        self.assertEqual(report.research_gap_score, 78.0)
        self.assertEqual(report.methodology_score, 82.0)
        self.assertEqual(report.contribution_score, 80.0)
        self.assertEqual(report.evidence_quality_score, 84.0)
        self.assertEqual(report.technical_strength_score, 88.0)
        self.assertEqual(report.clarity_score, 90.0)

        # Backward compatibility aliases
        self.assertEqual(report.rigor_score, 82.0)  # maps to methodology
        self.assertEqual(report.reproducibility_score, 84.0)  # maps to evidence quality
        self.assertEqual(report.ethical_score, 78.0)  # maps to research gap


# =============================================================================
# 2. Provenance & Versioned Re-evaluation Tests
# =============================================================================

class EvaluationProvenanceAndVersioningTest(AdvancedHardeningTestBase):
    """Test evaluation provenance, UUIDs, and versioned re-evaluation history."""

    def test_evaluation_provenance_fields_stored(self):
        """Evaluation report must store UUID, provider, versions, confidence, limitations."""
        evaluator = ResearchEvaluator()
        result = evaluator.evaluate_paper(self.paper_a)

        report = EvaluationReport.objects.get(evaluation_id=result['evaluation_id'])
        self.assertIsNotNone(report.evaluation_id)
        self.assertEqual(report.scoring_framework_version, 'v2-7dim-100pt')
        self.assertTrue(report.provider)
        self.assertTrue(report.model_version)
        self.assertIn(report.confidence, ['High', 'Medium', 'Low'])
        self.assertTrue(len(report.limitations) > 0)

    def test_versioned_reevaluation_preserves_history(self):
        """Re-evaluating a paper creates a new EvaluationReport version without deleting old."""
        evaluator = ResearchEvaluator()
        res1 = evaluator.evaluate_paper(self.paper_a)
        id1 = res1['evaluation_id']

        # Re-evaluate
        res2 = evaluator.evaluate_paper(self.paper_a, re_evaluate=True)
        id2 = res2['evaluation_id']

        self.assertNotEqual(id1, id2)
        reports = EvaluationReport.objects.filter(paper=self.paper_a).order_by('-paper_version')
        self.assertEqual(reports.count(), 2)
        self.assertEqual(reports[0].paper_version, 2)
        self.assertEqual(reports[1].paper_version, 1)

    def test_evaluation_report_view_renders_provenance_and_history(self):
        """Evaluation report view renders provenance metadata and version history."""
        self.client.login(username='alice_res', password='Password123!')
        evaluator = ResearchEvaluator()
        res = evaluator.evaluate_paper(self.paper_a)
        report = EvaluationReport.objects.get(evaluation_id=res['evaluation_id'])

        url = reverse('evaluation:report', args=[report.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'v2-7dim-100pt')
        self.assertContains(resp, 'Evaluation ID')
        self.assertContains(resp, str(report.evaluation_id)[:8])
        self.assertContains(resp, 'Academic Evaluation Disclaimer')


# =============================================================================
# 3. Source-Aware RAG & Citation Grounding Tests
# =============================================================================

class SourceAwareRAGTest(AdvancedHardeningTestBase):
    """Test source-aware chunking, citation grounding, and insufficient evidence fallback."""

    def setUp(self):
        super().setUp()
        self.chunk1 = PaperChunk.objects.create(
            paper=self.paper_a,
            chunk_index=0,
            content='We introduce the Transformer model based entirely on self-attention mechanisms.',
            section='Introduction',
            page_number=1,
            start_offset=0,
            end_offset=78,
        )
        self.chunk2 = PaperChunk.objects.create(
            paper=self.paper_a,
            chunk_index=1,
            content='Our training methodology uses Adam optimizer with beta1=0.9, beta2=0.98, and warmup steps=4000.',
            section='Methodology',
            page_number=4,
            start_offset=80,
            end_offset=175,
        )

    def test_chunk_stores_page_section_offsets(self):
        """PaperChunk must store page_number, section, and character offsets."""
        self.assertEqual(self.chunk2.page_number, 4)
        self.assertEqual(self.chunk2.section, 'Methodology')
        self.assertEqual(self.chunk2.start_offset, 80)
        self.assertEqual(self.chunk2.end_offset, 175)

    def test_rag_answers_with_numbered_citations(self):
        """RAG answerer includes source citations referencing section and page."""
        qa = ResearchQuestionAnswerer()
        result = qa.answer_question(
            paper=self.paper_a,
            question='What optimizer was used in the training methodology?'
        )
        self.assertIn('answer', result)
        self.assertIn('sources', result)
        self.assertGreater(len(result['sources']), 0)

        # Verify source metadata
        first_source = result['sources'][0]
        self.assertIn('section', first_source)
        self.assertIn('page_number', first_source)
        self.assertIn('snippet', first_source)

        # Answer should reference citations or context
        self.assertIn('[1]', result['answer'])

    def test_rag_insufficient_evidence_fallback(self):
        """When query has no relevant chunks or paper is empty, fallback message is returned."""
        # Create paper without chunks
        empty_paper = ResearchPaper.objects.create(
            title='Empty Whitepaper',
            abstract='No content yet.',
            research_area='AI_ML',
            status='UPLOADED',
            uploader=self.user_a,
        )
        qa = ResearchQuestionAnswerer()
        result = qa.answer_question(
            paper=empty_paper,
            question='What was the learning rate on page 100?'
        )
        self.assertEqual(result['answer'], qa.FALLBACK_NO_EVIDENCE)
        self.assertEqual(len(result['sources']), 0)

    def test_chat_message_saves_structured_sources(self):
        """ChatMessage model stores structured source citations in JSONField."""
        qa = ResearchQuestionAnswerer()
        result = qa.answer_question(
            paper=self.paper_a,
            question='Tell me about self-attention in the introduction.'
        )
        msg = ChatMessage.objects.filter(paper=self.paper_a).first()
        self.assertIsNotNone(msg)
        self.assertIsInstance(msg.sources, list)
        if msg.sources:
            self.assertIn('section', msg.sources[0])
            self.assertIn('page_number', msg.sources[0])


# =============================================================================
# 4. PDF Processing Robustness Tests
# =============================================================================

class PDFProcessingRobustnessTest(TestCase):
    """Test PDF processor section detection, corrupted PDF handling, and empty docs."""

    def test_section_pattern_detection(self):
        """Section detection regex identifies canonical academic sections."""
        processor = PaperProcessor()
        text_sample = (
            "ABSTRACT\nThis is the abstract summary.\n\n"
            "1. INTRODUCTION\nBackground on neural nets.\n\n"
            "3. METHODOLOGY AND EXPERIMENTAL SETUP\nWe trained on 8 GPUs.\n\n"
            "4. RESULTS\nTable 1 shows 94% accuracy.\n\n"
            "5. DISCUSSION AND LIMITATIONS\nSpeed vs memory trade-offs.\n\n"
            "6. CONCLUSION\nWe demonstrated state of the art.\n\n"
            "REFERENCES\n[1] Vaswani et al. 2017."
        )
        sections = processor._identify_sections(text_sample)
        detected_names = [s[0] for s in sections]

        self.assertIn('Abstract', detected_names)
        self.assertIn('Introduction', detected_names)
        self.assertIn('Methodology', detected_names)
        self.assertIn('Results', detected_names)
        self.assertIn('Discussion', detected_names)
        self.assertIn('Conclusion', detected_names)
        self.assertIn('References', detected_names)

    def test_corrupted_pdf_file_handling(self):
        """Corrupted or non-PDF bytes should return error without unhandled exception."""
        processor = PaperProcessor()
        corrupted_bytes = b"NOT_A_REAL_PDF_HEADER_JUST_GARBAGE_BYTES_12345"
        result = processor.extract_text_from_bytes(corrupted_bytes)

        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertEqual(result['page_count'], 0)

    def test_empty_paper_chunking_handling(self):
        """Empty text produces 0 chunks gracefully."""
        processor = PaperProcessor()
        chunks = processor.chunk_text("", chunk_size=500, overlap=50)
        self.assertEqual(len(chunks), 0)


# =============================================================================
# 5. Hybrid Search Engine Tests
# =============================================================================

class HybridSearchEngineTest(AdvancedHardeningTestBase):
    """Test multi-factor hybrid search ranking formula and faceted filtering."""

    def setUp(self):
        super().setUp()
        self.search_engine = HybridSearchEngine()

    def test_hybrid_search_ranking_weights(self):
        """Search engine weights must equal 0.60 semantic, 0.25 lexical, 0.10 area, 0.05 recency."""
        self.assertEqual(self.search_engine.WEIGHT_SEMANTIC, 0.60)
        self.assertEqual(self.search_engine.WEIGHT_LEXICAL, 0.25)
        self.assertEqual(self.search_engine.WEIGHT_AREA, 0.10)
        self.assertEqual(self.search_engine.WEIGHT_RECENCY, 0.05)
        total = (
            self.search_engine.WEIGHT_SEMANTIC +
            self.search_engine.WEIGHT_LEXICAL +
            self.search_engine.WEIGHT_AREA +
            self.search_engine.WEIGHT_RECENCY
        )
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_hybrid_search_scoring_and_transparency(self):
        """Search returns transparent breakdown of all 4 score components."""
        results = self.search_engine.search(query='attention transformer neural', area='AI_ML')
        self.assertTrue(len(results) > 0)
        top_match = results[0]

        self.assertEqual(top_match['paper'], self.paper_a)
        breakdown = top_match['breakdown']
        self.assertIn('semantic', breakdown)
        self.assertIn('lexical', breakdown)
        self.assertIn('area', breakdown)
        self.assertIn('recency', breakdown)
        self.assertIn('final_score', breakdown)
        self.assertIn('match_percentage', top_match)
        self.assertGreater(top_match['score'], 0)

    def test_hybrid_search_faceting_by_year_and_threshold(self):
        """Search respects year and minimum match threshold filters."""
        # Filter with threshold=90 should exclude weak matches
        res_high_thresh = self.search_engine.search(
            query='quantum cryptography',
            threshold=95
        )
        # Verify all returned papers meet threshold
        for r in res_high_thresh:
            self.assertGreaterEqual(r['match_percentage'], 95)

        # Filter by publication year
        current_year = timezone.now().year
        res_current = self.search_engine.search(
            query='neural network',
            year=current_year
        )
        for r in res_current:
            self.assertEqual(r['paper'].created_at.year, current_year)

    def test_search_view_handles_faceted_parameters(self):
        """Search view accepts area, year, author, and threshold GET parameters."""
        self.client.login(username='alice_res', password='Password123!')
        url = reverse('search:search')
        current_year = timezone.now().year
        resp = self.client.get(url, {
            'q': 'transformer',
            'area': 'AI_ML',
            'year': current_year,
            'threshold': 20
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Attention Is All You Need')
        self.assertContains(resp, 'Hybrid Ranking Formula')


# =============================================================================
# 6. Explainable Researcher Recommendations Tests
# =============================================================================

class ExplainableResearcherRecommendationsTest(AdvancedHardeningTestBase):
    """Test explainable recommendation components: shared interests, complementary skills, potential."""

    def setUp(self):
        super().setUp()
        self.int_ai = ResearchInterest.objects.create(name='Deep Learning')
        self.int_nlp = ResearchInterest.objects.create(name='NLP')
        self.int_cv = ResearchInterest.objects.create(name='Computer Vision')

        self.skill_py = Skill.objects.create(name='PyTorch')
        self.skill_math = Skill.objects.create(name='Linear Algebra')
        self.skill_deploy = Skill.objects.create(name='Kubernetes')

        # Alice has Deep Learning + NLP, PyTorch + Math
        self.researcher_a.interests.add(self.int_ai, self.int_nlp)
        self.researcher_a.skills.add(self.skill_py, self.skill_math)

        # Bob has Deep Learning + Computer Vision, Kubernetes
        self.researcher_b.interests.add(self.int_ai, self.int_cv)
        self.researcher_b.skills.add(self.skill_deploy)

    def test_recommendations_view_displays_explainable_factors(self):
        """Recommendation view shows shared interests, complementary skills, and potential badges."""
        self.client.login(username='alice_res', password='Password123!')
        url = reverse('collaboration:recommendations')
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        # Bob should be recommended to Alice
        self.assertContains(resp, 'Bob')
        # Shared interest Deep Learning
        self.assertContains(resp, 'Deep Learning')
        # Complementary skill Kubernetes
        self.assertContains(resp, 'Kubernetes')
        # Collaboration potential badge
        self.assertContains(resp, 'Collaboration Potential')


# =============================================================================
# 7. Security Boundaries & Authorization Tests
# =============================================================================

class SecurityBoundariesTest(AdvancedHardeningTestBase):
    """Test IDOR prevention, project boundaries, and CSRF protection."""

    def test_idor_paper_edit_forbidden_for_non_owner(self):
        """User B cannot edit User A's paper."""
        self.client.login(username='bob_res', password='Password123!')
        edit_url = reverse('papers:edit', args=[self.paper_a.pk])

        # GET should redirect or return 403 Forbidden
        resp_get = self.client.get(edit_url)
        self.assertIn(resp_get.status_code, [302, 403])

        # POST should redirect or return 403 Forbidden and not update paper
        resp_post = self.client.post(edit_url, {'title': 'Hacked Title'})
        self.assertIn(resp_post.status_code, [302, 403])
        self.paper_a.refresh_from_db()
        self.assertNotEqual(self.paper_a.title, 'Hacked Title')

    def test_idor_paper_delete_forbidden_for_non_owner(self):
        """User B cannot delete User A's paper."""
        self.client.login(username='bob_res', password='Password123!')
        delete_url = reverse('papers:delete', args=[self.paper_a.pk])

        # POST should redirect or return 403 and paper should still exist
        resp = self.client.post(delete_url)
        self.assertIn(resp.status_code, [302, 403])
        self.assertTrue(ResearchPaper.objects.filter(pk=self.paper_a.pk).exists())

    def test_project_boundary_non_member_cannot_edit(self):
        """User B cannot edit project owned/led by User A."""
        project = ResearchProject.objects.create(
            title='Autonomous Driving Platform',
            description='Perception algorithms',
            leader=self.user_a,
            research_area='AI_ML',
        )
        self.client.login(username='bob_res', password='Password123!')
        edit_url = reverse('projects:edit', args=[project.pk])

        resp = self.client.get(edit_url)
        self.assertIn(resp.status_code, [403, 404])

    def test_unauthenticated_requests_redirected_to_login(self):
        """Protected views redirect unauthenticated users to login page."""
        protected_urls = [
            reverse('papers:upload'),
            reverse('dashboard:home'),
            reverse('collaboration:recommendations'),
            reverse('projects:create'),
        ]
        for url in protected_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            self.assertIn(reverse('accounts:login'), resp.url)
