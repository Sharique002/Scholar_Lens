"""Regression tests for the application-wide UI redesign (shell, dashboard, auth pages)."""
from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from funding.models import FundingCall
from papers.models import ResearchPaper
from projects.models import Milestone, ProjectMember, ResearchProject


class DashboardRealDataTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ui_student', password='x')
        self.client.force_login(self.user)

    def test_no_fabricated_figures_on_empty_dashboard(self):
        r = self.client.get(reverse('dashboard:home'))
        content = r.content.decode()
        # The old dashboard invented these when no data existed.
        for fake in ('85.0 / 100', '94%', '88%', '100% RBAC'):
            self.assertNotIn(fake, content)
        self.assertEqual(r.context['summary']['publications'], 0)
        self.assertContains(r, 'No papers uploaded yet')
        self.assertContains(r, 'Nothing due soon')

    def test_summary_and_trend_reflect_database(self):
        ResearchPaper.objects.create(title='A', abstract='a', uploader=self.user, year=2023)
        ResearchPaper.objects.create(title='B', abstract='b', uploader=self.user, year=2023)
        ResearchPaper.objects.create(title='C', abstract='c', uploader=self.user, year=2024)
        ResearchPaper.objects.create(title='Ext', abstract='e', uploader=self.user, year=2024, is_external=True)
        r = self.client.get(reverse('dashboard:home'))
        self.assertEqual(r.context['summary']['publications'], 3)  # external papers are not institutional output
        self.assertEqual(r.context['publication_trend'], {'labels': ['2023', '2024'], 'values': [2, 1]})
        self.assertContains(r, 'id="publicationTrendData"')  # chart data goes through json_script

    def test_deadlines_merge_funding_and_own_milestones_only(self):
        FundingCall.objects.create(title='Soon Grant', sponsor='S', description='d', eligibility='e',
                                   deadline=timezone.now() + timedelta(days=5))
        mine = ResearchProject.objects.create(title='Mine', description='d', leader=self.user, research_area='AI_ML')
        other_owner = User.objects.create_user('other_lead', password='x')
        theirs = ResearchProject.objects.create(title='Theirs', description='d', leader=other_owner,
                                                research_area='AI_ML', is_public=True)
        Milestone.objects.create(project=mine, title='My milestone', due_date=date.today() + timedelta(days=3))
        Milestone.objects.create(project=theirs, title='Their milestone', due_date=date.today() + timedelta(days=2))
        r = self.client.get(reverse('dashboard:home'))
        titles = [d['title'] for d in r.context['upcoming_deadlines']]
        self.assertIn('Soon Grant', titles)
        self.assertIn('My milestone', titles)
        self.assertNotIn('Their milestone', titles)
        self.assertLess(titles.index('My milestone'), titles.index('Soon Grant'))  # soonest first

    def test_at_risk_limited_to_own_projects_for_non_staff(self):
        other = User.objects.create_user('lead2', password='x')
        theirs = ResearchProject.objects.create(title='T', description='d', leader=other, research_area='AI_ML')
        mine = ResearchProject.objects.create(title='M', description='d', leader=other, research_area='AI_ML')
        ProjectMember.objects.create(project=mine, user=self.user)
        Milestone.objects.create(project=theirs, title='Hidden risk', due_date=date.today(), risk='OVERDUE')
        Milestone.objects.create(project=mine, title='Visible risk', due_date=date.today(), risk='AT_RISK')
        r = self.client.get(reverse('dashboard:home'))
        self.assertContains(r, 'Visible risk')
        self.assertNotContains(r, 'Hidden risk')


class RoleNavigationTests(TestCase):
    def test_role_badge_and_queue_links(self):
        student = User.objects.create_user('nav_student', password='x')
        self.client.force_login(student)
        r = self.client.get(reverse('dashboard:home'))
        self.assertEqual(r.context['nav']['role'], 'Student')
        self.assertNotContains(r, f'href="{reverse("papers:author_queue")}"')
        self.assertNotContains(r, f'href="{reverse("analytics:research")}"')

        office = User.objects.create_user('nav_office', password='x', is_staff=True)
        self.client.force_login(office)
        r = self.client.get(reverse('dashboard:home'))
        self.assertEqual(r.context['nav']['role'], 'Research Office')
        self.assertContains(r, f'href="{reverse("papers:author_queue")}"')
        self.assertContains(r, f'href="{reverse("analytics:research")}"')

    def test_dean_sees_reports_by_group_not_username(self):
        dean = User.objects.create_user('plainname', password='x')
        dean.groups.add(Group.objects.get_or_create(name='Dean of Research')[0])
        self.client.force_login(dean)
        r = self.client.get(reverse('dashboard:home'))
        self.assertEqual(r.context['nav']['role'], 'Dean')
        self.assertContains(r, f'href="{reverse("analytics:research")}"')
        impostor = User.objects.create_user('dean_lookalike', password='x')
        self.client.force_login(impostor)
        self.assertNotContains(self.client.get(reverse('dashboard:home')), f'href="{reverse("analytics:research")}"')


class ShellInfrastructureTests(TestCase):
    def test_toast_region_and_confirm_dialog_present(self):
        user = User.objects.create_user('shell_user', password='x')
        self.client.force_login(user)
        r = self.client.get(reverse('dashboard:home'))
        self.assertContains(r, 'class="messages-container toast-region"')
        self.assertContains(r, 'id="confirmDialog"')
        self.assertContains(r, 'href="#main" class="skip-link"')

    def test_login_hides_demo_credentials_outside_debug(self):
        r = self.client.get(reverse('accounts:login'))  # tests run with DEBUG=False
        self.assertNotContains(r, 'Admin@12345')
        self.assertContains(r, 'Sign In with Google')
        self.assertContains(r, 'autocomplete="current-password"')

    def test_failed_login_does_not_echo_password(self):
        r = self.client.post(reverse('accounts:login'), {'username': 'nobody', 'password': 'S3cretTyped!'})
        self.assertNotContains(r, 'S3cretTyped!')
