import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.management import call_command

from researchers.models import ResearcherProfile, ResearchInterest, Skill, Department
from papers.models import ResearchPaper, PaperAuthor
from projects.models import ResearchProject, ProjectMember
from collaboration.models import CollaborationSuggestion


class CollaborationSuggestionsTest(TestCase):
    def setUp(self):
        self.dept_cs = Department.objects.create(name='Computer Science', code='CS')
        self.dept_bio = Department.objects.create(name='Bioinformatics', code='BIO')

        self.user1 = User.objects.create_user(username='dr_smith', password='Password123!', email='smith@uni.edu')
        self.profile1 = ResearcherProfile.objects.create(
            user=self.user1,
            department=self.dept_cs,
            is_available_for_collaboration=True,
            verification_status='VERIFIED'
        )

        self.user2 = User.objects.create_user(username='dr_patel', password='Password123!', email='patel@uni.edu')
        self.profile2 = ResearcherProfile.objects.create(
            user=self.user2,
            department=self.dept_bio,
            is_available_for_collaboration=True,
            verification_status='VERIFIED'
        )

        self.user3 = User.objects.create_user(username='dr_lee', password='Password123!', email='lee@uni.edu')
        self.profile3 = ResearcherProfile.objects.create(
            user=self.user3,
            department=self.dept_cs,
            is_available_for_collaboration=True
        )

        self.int_ai = ResearchInterest.objects.create(name='Machine Learning')
        self.int_genomics = ResearchInterest.objects.create(name='Genomics')
        self.skill_python = Skill.objects.create(name='Python')
        self.skill_r = Skill.objects.create(name='R Stats')

        self.profile1.interests.add(self.int_ai)
        self.profile1.skills.add(self.skill_python)

        self.profile2.interests.add(self.int_ai, self.int_genomics)
        self.profile2.skills.add(self.skill_r)

    def test_score_pair_with_adjacency_and_gap(self):
        from collaboration.suggestions import score_pair
        score, adj, gap, expl = score_pair(self.profile1, self.profile2)

        # They share 'Machine Learning', have complementary skill 'R Stats', different departments,
        # and have never co-authored or shared a project => gap bonus applied
        self.assertGreater(adj, 0)
        self.assertEqual(gap, 30.0)
        self.assertIn('Machine Learning', expl['shared_interests'])
        self.assertTrue(expl['is_cross_department'])
        self.assertFalse(expl['has_coauthored'])

    def test_coauthorship_eliminates_gap_bonus(self):
        from collaboration.suggestions import score_pair
        # Create a paper co-authored by profile1 and profile2
        paper = ResearchPaper.objects.create(title='Joint Paper', status='PROCESSED', uploader=self.user1)
        PaperAuthor.objects.create(paper=paper, name='Dr Smith', researcher=self.profile1, order=1)
        PaperAuthor.objects.create(paper=paper, name='Dr Patel', researcher=self.profile2, order=2)

        score, adj, gap, expl = score_pair(self.profile1, self.profile2)
        self.assertEqual(gap, 0.0)
        self.assertTrue(expl['has_coauthored'])

    def test_compute_collaboration_suggestions_command(self):
        call_command('compute_collaboration_suggestions')
        suggestions = CollaborationSuggestion.objects.filter(researcher=self.profile1)
        self.assertTrue(suggestions.exists())
        top = suggestions.first()
        self.assertEqual(top.suggested, self.profile2)
        self.assertFalse(top.is_dismissed)

    def test_dismiss_suggestion(self):
        call_command('compute_collaboration_suggestions')
        sug = CollaborationSuggestion.objects.filter(researcher=self.profile1, suggested=self.profile2).first()
        self.assertIsNotNone(sug)

        client = Client()
        client.login(username='dr_smith', password='Password123!')
        url = reverse('collaboration:dismiss_suggestion', args=[sug.pk])
        resp = client.post(url)
        self.assertEqual(resp.status_code, 302)

        sug.refresh_from_db()
        self.assertTrue(sug.is_dismissed)

    def test_collaboration_graph_data_endpoint(self):
        call_command('compute_collaboration_suggestions')
        client = Client()
        client.login(username='dr_smith', password='Password123!')

        resp = client.get(reverse('collaboration:graph_data'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('nodes', data)
        self.assertIn('edges', data)
        node_ids = [n['data']['id'] for n in data['nodes']]
        self.assertIn(str(self.profile1.pk), node_ids)
        self.assertIn(str(self.profile2.pk), node_ids)

    def test_collaboration_graph_page_and_accessible_table(self):
        call_command('compute_collaboration_suggestions')
        client = Client()
        client.login(username='dr_smith', password='Password123!')

        resp = client.get(reverse('collaboration:graph'))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')
        # Cytoscape container
        self.assertIn('id="cy"', content)
        # Accessible HTML table fallback
        self.assertIn('<table', content)
        self.assertIn('dr_smith', content)
        self.assertIn('dr_patel', content)
