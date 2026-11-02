"""Tests for M2 Author disambiguation, name variant matching, and review queue."""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from researchers.models import ResearcherProfile, Department
from papers.models import ResearchPaper, PaperAuthor
from papers.authors import match_authors, normalise_name, name_score
from dashboard.models import AuditEntry


class AuthorDisambiguationTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('office_staff', password='password123', is_staff=True)
        self.student = User.objects.create_user('student_user', password='password123')

        self.dept_cse = Department.objects.create(name='Computer Science and Engineering', code='CSE')
        self.dept_bio = Department.objects.create(name='Biotechnology', code='BIO')

        self.user_rajesh = User.objects.create_user('rajesh_k', first_name='Rajesh', last_name='Kumar')
        self.profile_rajesh = ResearcherProfile.objects.create(
            user=self.user_rajesh,
            department=self.dept_cse,
            orcid_id='0000-0002-1825-0097'
        )

        self.user_ramesh = User.objects.create_user('ramesh_k', first_name='Ramesh', last_name='Kumar')
        self.profile_ramesh = ResearcherProfile.objects.create(
            user=self.user_ramesh,
            department=self.dept_bio,
            orcid_id='0000-0001-5000-0000'
        )

    def test_author_name_variants(self):
        # 1. Full name with accents, uppercase, reverse comma
        paper1 = ResearchPaper.objects.create(title="Study 1 on Deep Learning", year=2023)
        a1 = PaperAuthor.objects.create(paper=paper1, name="Rajésh Kumar", order=1)
        a2 = PaperAuthor.objects.create(paper=paper1, name="Kumar, Rajesh", order=2)
        a3 = PaperAuthor.objects.create(paper=paper1, name="RAJESH KUMAR", order=3)

        match_authors(paper1)

        a1.refresh_from_db()
        a2.refresh_from_db()
        a3.refresh_from_db()

        self.assertEqual(a1.researcher, self.profile_rajesh)
        self.assertEqual(a1.match_status, 'CONFIRMED')
        self.assertGreaterEqual(a1.match_score, 92.0)

        self.assertEqual(a2.researcher, self.profile_rajesh)
        self.assertEqual(a2.match_status, 'CONFIRMED')

        self.assertEqual(a3.researcher, self.profile_rajesh)
        self.assertEqual(a3.match_status, 'CONFIRMED')

        # 2. Ambiguous initial: "R. Kumar" from another department or with multiple candidates
        # Must go to PENDING_REVIEW instead of auto-matching!
        paper2 = ResearchPaper.objects.create(title="Study 2 on Genetics", year=2023)
        a_ambig = PaperAuthor.objects.create(paper=paper2, name="R. Kumar", order=1)

        match_authors(paper2)

        a_ambig.refresh_from_db()
        self.assertEqual(a_ambig.match_status, 'PENDING_REVIEW')
        self.assertNotEqual(a_ambig.match_status, 'CONFIRMED')

    def test_orcid_exact_match(self):
        paper = ResearchPaper.objects.create(title="ORCID Matched Paper", year=2024)
        author = PaperAuthor.objects.create(
            paper=paper,
            name="R. K.",
            orcid='0000-0002-1825-0097',
            order=1
        )
        match_authors(paper)

        author.refresh_from_db()
        self.assertEqual(author.researcher, self.profile_rajesh)
        self.assertEqual(author.match_status, 'CONFIRMED')
        self.assertEqual(author.match_score, 100.0)

    def test_author_queue_confirm_and_reject(self):
        paper = ResearchPaper.objects.create(title="Ambiguous Paper", year=2023)
        author = PaperAuthor.objects.create(
            paper=paper,
            name="R. Kumar",
            researcher=self.profile_rajesh,
            match_status='PENDING_REVIEW',
            match_score=85.0,
            order=1
        )

        # Non-staff cannot view queue
        self.client.force_login(self.student)
        res_queue_forbidden = self.client.get(reverse('papers:author_queue'))
        self.assertEqual(res_queue_forbidden.status_code, 403)

        # Staff can view queue
        self.client.force_login(self.staff)
        res_queue = self.client.get(reverse('papers:author_queue'))
        self.assertEqual(res_queue.status_code, 200)
        self.assertContains(res_queue, "R. Kumar")

        # Staff confirms match
        decide_url = reverse('papers:author_decide', args=[author.id])
        res_confirm = self.client.post(decide_url, {'action': 'confirm', 'researcher_id': self.profile_rajesh.pk}, follow=True)
        self.assertEqual(res_confirm.status_code, 200)

        author.refresh_from_db()
        self.assertEqual(author.match_status, 'CONFIRMED')
        self.assertEqual(author.matched_by, self.staff)

        # Check audit entry
        audit = AuditEntry.objects.filter(target_type='papers.paperauthor', target_id=author.id, action='author.confirmed')
        self.assertTrue(audit.exists())

        # Create another author to test rejection
        author2 = PaperAuthor.objects.create(
            paper=paper,
            name="Another Author",
            researcher=self.profile_ramesh,
            match_status='PENDING_REVIEW',
            match_score=81.0,
            order=2
        )
        res_reject = self.client.post(reverse('papers:author_decide', args=[author2.id]), {'action': 'reject'}, follow=True)
        self.assertEqual(res_reject.status_code, 200)

        author2.refresh_from_db()
        self.assertEqual(author2.match_status, 'REJECTED')
        self.assertIsNone(author2.researcher)

        # Check audit entry for rejection
        audit_rej = AuditEntry.objects.filter(target_type='papers.paperauthor', target_id=author2.id, action='author.rejected')
        self.assertTrue(audit_rej.exists())
