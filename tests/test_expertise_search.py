"""Tests for M3 Stored search document and faceted expertise search."""
import time
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.management import call_command

from researchers.models import ResearcherProfile, Department, ResearchInterest, Skill
from researchers.search_index import refresh_search_document


class ExpertiseSearchTests(TestCase):
    def setUp(self):
        self.dept_cse = Department.objects.create(name='Computer Science and Engineering', code='CSE')
        self.dept_bio = Department.objects.create(name='Biotechnology', code='BIO')

        self.interest_robotics = ResearchInterest.objects.create(name='Robotics', category='Domain')
        self.interest_genetics = ResearchInterest.objects.create(name='Genetics', category='Domain')

        # Researcher A: Interest = Robotics (Weight A)
        self.user_a = User.objects.create_user('user_a', first_name='Alice', last_name='Smith')
        self.profile_a = ResearcherProfile.objects.create(
            user=self.user_a,
            department=self.dept_cse,
            headline='AI & Robotics Scientist',
            is_available_for_collaboration=True
        )
        self.profile_a.interests.add(self.interest_robotics)

        # Researcher B: Robotics only in summary (Weight C)
        self.user_b = User.objects.create_user('user_b', first_name='Bob', last_name='Jones')
        self.profile_b = ResearcherProfile.objects.create(
            user=self.user_b,
            department=self.dept_bio,
            headline='Molecular Biologist',
            expertise_summary='Experienced with lab automated robotics systems in biochemical assays.',
            is_available_for_collaboration=False
        )
        self.profile_b.interests.add(self.interest_genetics)

        refresh_search_document([self.profile_a.pk, self.profile_b.pk])

    def test_search_weights_ranking(self):
        self.client.force_login(self.user_a)
        url = reverse('search:expertise')
        res = self.client.get(url, {'q': 'Robotics'})
        self.assertEqual(res.status_code, 200)

        results = list(res.context['page_obj'])
        self.assertGreaterEqual(len(results), 2)
        # Profile A has Robotics in interests (Weight A), so it should rank higher than B (Weight C)
        self.assertEqual(results[0].pk, self.profile_a.pk)
        self.assertEqual(results[1].pk, self.profile_b.pk)

    def test_faceted_filters(self):
        self.client.force_login(self.user_a)
        url = reverse('search:expertise')

        # Filter by department CSE
        res_cse = self.client.get(url, {'department': 'CSE'})
        self.assertEqual(res_cse.status_code, 200)
        pks_cse = [p.pk for p in res_cse.context['page_obj']]
        self.assertIn(self.profile_a.pk, pks_cse)
        self.assertNotIn(self.profile_b.pk, pks_cse)

        # Filter by availability
        res_avail = self.client.get(url, {'availability': 'true'})
        self.assertEqual(res_avail.status_code, 200)
        pks_avail = [p.pk for p in res_avail.context['page_obj']]
        self.assertIn(self.profile_a.pk, pks_avail)
        self.assertNotIn(self.profile_b.pk, pks_avail)

    def test_under_one_second(self):
        # Bulk create 2,000 dummy users and profiles to verify sub-second GIN index search query
        users = [
            User(username=f'bench_user_{i}', first_name=f'Bench{i}', last_name=f'Researcher{i}')
            for i in range(2000)
        ]
        User.objects.bulk_create(users)

        created_users = list(User.objects.filter(username__startswith='bench_user_'))
        profiles = [
            ResearcherProfile(
                user=u,
                department=self.dept_cse if i % 2 == 0 else self.dept_bio,
                headline=f"Researcher in topic {i % 50}",
                expertise_summary=f"Summary describing research on topic {i % 50} and algorithmic systems"
            )
            for i, u in enumerate(created_users)
        ]
        ResearcherProfile.objects.bulk_create(profiles)

        # Index them
        created_pks = [p.pk for p in ResearcherProfile.objects.filter(user__username__startswith='bench_user_')]
        refresh_search_document(created_pks[:100])  # index a batch with search document

        self.client.force_login(self.user_a)
        start = time.perf_counter()
        res = self.client.get(reverse('search:expertise'), {'q': 'Robotics'})
        elapsed = time.perf_counter() - start

        self.assertEqual(res.status_code, 200)
        self.assertLess(
            elapsed, 1.0,
            f"Expertise search took {elapsed:.3f}s on 2000 profiles, expected < 1.0s"
        )
