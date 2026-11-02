"""Tests for M2 Duplicate detection, review queue, and reversible merges."""
import json
import os
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings

from papers.models import ResearchPaper, DuplicateCandidate
from papers.dedup import find_duplicate, merge, unmerge, evaluate_pair
from dashboard.models import AuditEntry


class DuplicateDetectionAccuracyTests(TestCase):
    def test_fixture_accuracy_at_least_95(self):
        fixture_path = os.path.join(settings.BASE_DIR, 'tests', 'fixtures', 'dedup_pairs.json')
        with open(fixture_path, 'r', encoding='utf-8') as f:
            pairs = json.load(f)

        correct = 0
        total = len(pairs)
        failures = []

        for p in pairs:
            # evaluate_pair takes title_a, year_a, doi_a, title_b, year_b, doi_b
            # and returns (predicted_is_duplicate, score, action)
            pred_dup, score, action = evaluate_pair(
                p['title_a'], p['year_a'], p.get('doi_a'),
                p['title_b'], p['year_b'], p.get('doi_b')
            )
            expected = p['is_duplicate']
            if pred_dup == expected:
                correct += 1
            else:
                failures.append({
                    'pair': (p['title_a'], p['title_b']),
                    'expected': expected,
                    'pred': pred_dup,
                    'action': action,
                    'score': score,
                    'note': p.get('note')
                })

        accuracy = correct / total
        self.assertGreaterEqual(
            accuracy, 0.95,
            f"Deduplication fixture accuracy was {accuracy*100:.1f}% ({correct}/{total}), expected >= 95%. Failures: {failures[:5]}"
        )


class DuplicateBehaviorTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('office_staff', password='password123', is_staff=True)
        self.student = User.objects.create_user('student_user', password='password123')
        self.author = User.objects.create_user('author_user', password='password123')

    def test_short_generic_titles_never_auto_merge(self):
        # Two papers with titles < 4 words: "Editorial" or "Introduction"
        paper1 = ResearchPaper.objects.create(
            title="Introduction",
            abstract="Editorial introduction to the special issue.",
            uploader=self.author,
            year=2023
        )
        dup, score, action = find_duplicate("Introduction", year=2023)
        self.assertEqual(dup.id, paper1.id)
        # Even though exact match, must be REVIEW, never AUTO_MERGE
        self.assertEqual(action, 'REVIEW')
        self.assertNotEqual(action, 'AUTO_MERGE')

    def test_matching_doi_is_always_auto_merge(self):
        paper = ResearchPaper.objects.create(
            title="A Preliminary Study on Quantum Algorithms",
            abstract="Quantum abstract",
            uploader=self.author,
            year=2022,
            doi="10.1103/PhysRevA.100.012345"
        )
        dup, score, action = find_duplicate("Different Title Presentation Format", year=2022, doi="10.1103/PhysRevA.100.012345")
        self.assertEqual(dup.id, paper.id)
        self.assertEqual(action, 'AUTO_MERGE')
        self.assertEqual(score, 100.0)

    def test_unmerge_restores_and_is_idempotent(self):
        paper_a = ResearchPaper.objects.create(
            title="Original Study on Attention Mechanisms",
            abstract="Abstract A",
            uploader=self.author,
            year=2020
        )
        paper_b = ResearchPaper.objects.create(
            title="Attention Mechanisms: A Study",
            abstract="Abstract B",
            uploader=self.author,
            year=2020
        )

        # Merge B into A
        merge(paper_b, paper_a, actor=self.staff)
        paper_b.refresh_from_db()
        self.assertEqual(paper_b.merged_into, paper_a)
        self.assertNotIn(paper_b, list(ResearchPaper.objects.all()))

        # Check audit entry for merge
        merge_audit = AuditEntry.objects.filter(target_type='papers.researchpaper', target_id=paper_b.id, action='paper.merged')
        self.assertTrue(merge_audit.exists())
        self.assertEqual(merge_audit.first().actor, self.staff)

        # Unmerge
        unmerge(paper_b, actor=self.staff)
        paper_b.refresh_from_db()
        self.assertIsNone(paper_b.merged_into)
        self.assertIn(paper_b, list(ResearchPaper.objects.all()))

        # Check audit entry for unmerge
        unmerge_audit = AuditEntry.objects.filter(target_type='papers.researchpaper', target_id=paper_b.id, action='paper.unmerged')
        self.assertTrue(unmerge_audit.exists())

        # Unmerge a second time (idempotent, no error)
        unmerge(paper_b, actor=self.staff)
        paper_b.refresh_from_db()
        self.assertIsNone(paper_b.merged_into)

    def test_dedup_review_queue_and_actions(self):
        canonical = ResearchPaper.objects.create(
            title="Foundations of Large Language Models",
            abstract="Canonical LLM paper",
            uploader=self.author,
            year=2023
        )
        incoming = ResearchPaper.objects.create(
            title="Foundations of Large Language Model",
            abstract="Duplicate candidate incoming",
            uploader=self.author,
            year=2023
        )
        candidate = DuplicateCandidate.objects.create(
            incoming_paper=incoming,
            existing_paper=canonical,
            similarity_score=91.5,
            status='PENDING'
        )

        # Non-staff cannot view queue
        self.client.force_login(self.student)
        res_queue_forbidden = self.client.get(reverse('papers:dedup_queue'))
        self.assertEqual(res_queue_forbidden.status_code, 403)

        # Staff can view queue
        self.client.force_login(self.staff)
        res_queue = self.client.get(reverse('papers:dedup_queue'))
        self.assertEqual(res_queue.status_code, 200)
        self.assertContains(res_queue, "Foundations of Large Language Models")

        # Staff decides: merge
        decide_url = reverse('papers:dedup_decide', args=[candidate.id])
        res_merge = self.client.post(decide_url, {'action': 'merge'}, follow=True)
        self.assertEqual(res_merge.status_code, 200)

        candidate.refresh_from_db()
        incoming.refresh_from_db()
        self.assertEqual(candidate.status, 'MERGED')
        self.assertEqual(candidate.reviewed_by, self.staff)
        self.assertEqual(incoming.merged_into, canonical)

        # Create another candidate and test dismiss
        incoming2 = ResearchPaper.objects.create(
            title="Another Language Model Paper",
            abstract="Another paper",
            uploader=self.author,
            year=2023
        )
        candidate2 = DuplicateCandidate.objects.create(
            incoming_paper=incoming2,
            existing_paper=canonical,
            similarity_score=82.0,
            status='PENDING'
        )
        res_dismiss = self.client.post(reverse('papers:dedup_decide', args=[candidate2.id]), {'action': 'dismiss'}, follow=True)
        self.assertEqual(res_dismiss.status_code, 200)

        candidate2.refresh_from_db()
        incoming2.refresh_from_db()
        self.assertEqual(candidate2.status, 'DISMISSED')
        self.assertIsNone(incoming2.merged_into)
