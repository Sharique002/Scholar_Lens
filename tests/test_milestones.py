"""Tests for M7 Project Milestones and Dependency Rules."""
from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from projects.models import ResearchProject, ProjectMember, Milestone
from projects.forms import MilestoneForm


class MilestoneTests(TestCase):
    def setUp(self):
        self.leader = User.objects.create_user('proj_leader', password='password123')
        self.member = User.objects.create_user('proj_member', password='password123')
        self.outsider = User.objects.create_user('outsider_user', password='password123')

        self.project = ResearchProject.objects.create(
            title="AI Medical Diagnosis",
            description="Diagnostic neural net.",
            leader=self.leader,
            research_area="AI",
            status="ACTIVE",
            is_public=True
        )
        ProjectMember.objects.create(project=self.project, user=self.leader, role='LEADER')
        ProjectMember.objects.create(project=self.project, user=self.member, role='RESEARCHER')

        self.other_project = ResearchProject.objects.create(
            title="Quantum Hardware",
            description="Quantum gates.",
            leader=self.leader,
            research_area="OTHER",
            status="ACTIVE",
            is_public=True
        )

        self.private_project = ResearchProject.objects.create(
            title="Classified Defense Analysis",
            description="Private project.",
            leader=self.leader,
            research_area="SEC",
            status="ACTIVE",
            is_public=False
        )

    def test_leader_creates_milestone(self):
        self.client.force_login(self.leader)
        url = reverse('projects:milestone_create', args=[self.project.pk])
        due = date.today() + timedelta(days=10)
        data = {
            'title': 'Dataset Collection',
            'is_deliverable': True,
            'owner': self.member.pk,
            'start_date': date.today(),
            'due_date': due,
            'status': 'PLANNED',
            'progress': 0,
        }
        res = self.client.post(url, data, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(Milestone.objects.filter(project=self.project, title='Dataset Collection').exists())

    def test_member_cannot_create(self):
        self.client.force_login(self.member)
        url = reverse('projects:milestone_create', args=[self.project.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 404)

    def test_owner_updates_progress(self):
        m = Milestone.objects.create(
            project=self.project,
            title="Model Training",
            owner=self.member,
            due_date=date.today() + timedelta(days=5),
            status='PLANNED',
            progress=10
        )
        self.client.force_login(self.member)
        url = reverse('projects:milestone_progress', args=[m.pk])
        res = self.client.post(url, {'status': 'IN_PROGRESS', 'progress': 60}, follow=True)
        self.assertEqual(res.status_code, 200)
        m.refresh_from_db()
        self.assertEqual(m.status, 'IN_PROGRESS')
        self.assertEqual(m.progress, 60)

    def test_done_sets_progress_and_completed_on(self):
        m = Milestone.objects.create(
            project=self.project,
            title="Clinical Validation",
            owner=self.member,
            due_date=date.today() - timedelta(days=2),
            status='IN_PROGRESS',
            progress=50,
            risk='OVERDUE',
            risk_reason='Was due 2 days ago'
        )
        m.status = 'DONE'
        m.save()

        m.refresh_from_db()
        self.assertEqual(m.progress, 100)
        self.assertEqual(m.completed_on, date.today())
        self.assertEqual(m.risk, 'ON_TRACK')
        self.assertEqual(m.risk_reason, '')

    def test_dependency_cycle_rejected(self):
        # A depends on B. Then editing B to depend on A should fail.
        m_b = Milestone.objects.create(
            project=self.project,
            title="Milestone B",
            due_date=date.today() + timedelta(days=10)
        )
        m_a = Milestone.objects.create(
            project=self.project,
            title="Milestone A",
            due_date=date.today() + timedelta(days=20)
        )
        m_a.depends_on.add(m_b)

        # Try setting B to depend on A via MilestoneForm
        form = MilestoneForm(
            data={
                'title': 'Milestone B',
                'due_date': date.today() + timedelta(days=10),
                'status': 'PLANNED',
                'progress': 0,
                'depends_on': [m_a.pk]
            },
            instance=m_b,
            project=self.project
        )
        self.assertFalse(form.is_valid())
        self.assertIn("That would create a loop", str(form.errors))

    def test_self_dependency_rejected(self):
        m = Milestone.objects.create(
            project=self.project,
            title="Self-dependent Milestone",
            due_date=date.today() + timedelta(days=10)
        )
        form = MilestoneForm(
            data={
                'title': 'Self-dependent Milestone',
                'due_date': date.today() + timedelta(days=10),
                'status': 'PLANNED',
                'progress': 0,
                'depends_on': [m.pk]
            },
            instance=m,
            project=self.project
        )
        self.assertFalse(form.is_valid())
        self.assertIn("A milestone can't depend on itself.", form.errors['depends_on'])

    def test_dependency_limited_to_same_project(self):
        other_m = Milestone.objects.create(
            project=self.other_project,
            title="Other Project Milestone",
            due_date=date.today() + timedelta(days=15)
        )
        form = MilestoneForm(project=self.project)
        self.assertNotIn(other_m, form.fields['depends_on'].queryset)

    def test_private_project_milestones_hidden(self):
        self.client.force_login(self.outsider)
        url = reverse('projects:milestones', args=[self.private_project.pk])
        res = self.client.get(url, follow=True)
        self.assertRedirects(res, reverse('projects:list'))
        messages_list = [m.message for m in res.context['messages']]
        self.assertTrue(any("You don't have access" in m for m in messages_list))
