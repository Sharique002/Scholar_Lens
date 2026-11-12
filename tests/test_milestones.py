"""Tests for M7 Project Milestones and Dependency Rules."""
from io import StringIO
from datetime import date, timedelta
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.management import call_command
from projects.models import ResearchProject, ProjectMember, Milestone
from projects.forms import MilestoneForm
from projects.risk import compute_risk, run_risk_check
from dashboard.models import ResearchActivity


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
        self.assertEqual(m.completed_on, timezone.localdate())
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

    def test_timeline_bar_positions(self):
        # Project 1 Jan to 31 Jan (30-day span)
        proj = ResearchProject.objects.create(
            title="Gantt Timeline Project",
            description="Testing bar calculations.",
            leader=self.leader,
            research_area="AI",
            status="ACTIVE",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            is_public=True
        )
        # Milestone from 1 Jan to 16 Jan (15 days / 30 days = 50.0%)
        Milestone.objects.create(
            project=proj,
            title="Halfway Milestone",
            start_date=date(2026, 1, 1),
            due_date=date(2026, 1, 16),
            status="PLANNED"
        )
        self.client.force_login(self.leader)
        res = self.client.get(reverse('projects:milestones', args=[proj.pk]))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'style="left:0.0%;width:50.0%"')

    def test_timeline_empty_state(self):
        empty_proj = ResearchProject.objects.create(
            title="Empty Milestones Project",
            description="No milestones.",
            leader=self.leader,
            research_area="AI",
            status="ACTIVE",
            is_public=True
        )
        self.client.force_login(self.leader)
        res = self.client.get(reverse('projects:milestones', args=[empty_proj.pk]))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "No milestones yet.")
        self.assertContains(res, "Add the first milestone")


class MilestoneRiskTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff_lead', password='password123', is_staff=True)
        self.leader = User.objects.create_user('risk_leader', password='password123')
        self.owner = User.objects.create_user('risk_owner', password='password123')
        self.today = date(2026, 11, 2)

        self.project = ResearchProject.objects.create(
            title="Autonomic Vehicles",
            description="LIDAR and sensor fusion.",
            leader=self.leader,
            research_area="AI",
            status="ACTIVE",
            is_public=True
        )

    def test_rule_1_done_is_on_track(self):
        m = Milestone(status='DONE', due_date=self.today - timedelta(days=5), progress=100)
        risk, reason = compute_risk(m, today=self.today, days=7, min_progress=50)
        self.assertEqual(risk, 'ON_TRACK')
        self.assertEqual(reason, '')

    def test_rule_2_past_due_is_overdue(self):
        m = Milestone(status='IN_PROGRESS', due_date=self.today - timedelta(days=3), progress=80)
        risk, reason = compute_risk(m, today=self.today, days=7, min_progress=50)
        self.assertEqual(risk, 'OVERDUE')
        self.assertIn('Was due', reason)

    def test_rule_3_near_due_low_progress_is_at_risk(self):
        m = Milestone(status='IN_PROGRESS', due_date=self.today + timedelta(days=4), progress=20)
        risk, reason = compute_risk(m, today=self.today, days=7, min_progress=50)
        self.assertEqual(risk, 'AT_RISK')
        self.assertIn('Due in 4 days, only 20% done', reason)

    def test_rule_4_dependency_blocked_is_at_risk(self):
        m_dep = Milestone.objects.create(
            project=self.project,
            title="Hardware Setup",
            due_date=self.today + timedelta(days=12),
            status='IN_PROGRESS',
            risk='OVERDUE'
        )
        m = Milestone.objects.create(
            project=self.project,
            title="Software Benchmark",
            due_date=self.today + timedelta(days=15),
            status='PLANNED',
            progress=0
        )
        m.depends_on.add(m_dep)
        risk, reason = compute_risk(m, today=self.today, days=7, min_progress=50)
        self.assertEqual(risk, 'AT_RISK')
        self.assertEqual(reason, 'Waiting on "Hardware Setup"')

    def test_rule_5_otherwise_is_on_track(self):
        m = Milestone(project=self.project, status='IN_PROGRESS', due_date=self.today + timedelta(days=20), progress=10)
        risk, reason = compute_risk(m, today=self.today, days=7, min_progress=50)
        self.assertEqual(risk, 'ON_TRACK')
        self.assertEqual(reason, '')

    def test_thresholds_configurable(self):
        m = Milestone.objects.create(
            project=self.project,
            title="Threshold Test Milestone",
            due_date=self.today + timedelta(days=6),
            progress=20,
            status='IN_PROGRESS'
        )
        # With days=3, 6 days left is ON_TRACK
        res3 = run_risk_check(today=self.today, days=3, min_progress=50)
        m.refresh_from_db()
        self.assertEqual(m.risk, 'ON_TRACK')

        # With days=10, 6 days left is AT_RISK
        res10 = run_risk_check(today=self.today, days=10, min_progress=50)
        m.refresh_from_db()
        self.assertEqual(m.risk, 'AT_RISK')

    def test_notifies_only_on_change(self):
        m = Milestone.objects.create(
            project=self.project,
            title="Notification Test",
            owner=self.owner,
            due_date=self.today - timedelta(days=1),
            status='IN_PROGRESS'
        )
        # First run: changes risk from ON_TRACK to OVERDUE -> sends notification
        run_risk_check(today=self.today, days=7, min_progress=50)
        notif_count = ResearchActivity.objects.filter(activity_type='MILESTONE').count()
        self.assertGreaterEqual(notif_count, 1)

        # Second run: risk is already OVERDUE -> no new notification
        run_risk_check(today=self.today, days=7, min_progress=50)
        self.assertEqual(ResearchActivity.objects.filter(activity_type='MILESTONE').count(), notif_count)

    def test_due_notice_once(self):
        m = Milestone.objects.create(
            project=self.project,
            title="Due Notice Test",
            owner=self.owner,
            due_date=self.today + timedelta(days=5),
            progress=60,
            status='IN_PROGRESS'
        )
        run_risk_check(today=self.today, days=7, min_progress=50)
        m.refresh_from_db()
        self.assertTrue(m.due_notified)
        initial_notifs = ResearchActivity.objects.filter(description__contains="is due on").count()
        self.assertEqual(initial_notifs, 2)  # owner + leader

        # Run again: should not resend
        run_risk_check(today=self.today, days=7, min_progress=50)
        self.assertEqual(ResearchActivity.objects.filter(description__contains="is due on").count(), initial_notifs)

    def test_dependency_overdue_propagates_same_run(self):
        dep = Milestone.objects.create(
            project=self.project,
            title="Dependency 1",
            due_date=self.today - timedelta(days=2),
            status='IN_PROGRESS'
        )
        main_m = Milestone.objects.create(
            project=self.project,
            title="Main Milestone",
            due_date=self.today + timedelta(days=20),
            status='PLANNED',
            progress=10
        )
        main_m.depends_on.add(dep)

        # In pass 1, dep becomes OVERDUE. In pass 2, main_m detects dep is OVERDUE and becomes AT_RISK!
        run_risk_check(today=self.today, days=7, min_progress=50)
        dep.refresh_from_db()
        main_m.refresh_from_db()
        self.assertEqual(dep.risk, 'OVERDUE')
        self.assertEqual(main_m.risk, 'AT_RISK')
        self.assertIn("Waiting on", main_m.risk_reason)

    def test_board_staff_only(self):
        Milestone.objects.create(
            project=self.project,
            title="Overdue Flagged",
            due_date=self.today - timedelta(days=4),
            status='IN_PROGRESS',
            risk='OVERDUE'
        )
        # Non-staff gets 403
        self.client.force_login(self.leader)
        res_non = self.client.get(reverse('projects:at_risk'))
        self.assertEqual(res_non.status_code, 403)

        # Staff gets 200
        self.client.force_login(self.staff)
        res_staff = self.client.get(reverse('projects:at_risk'))
        self.assertEqual(res_staff.status_code, 200)
        self.assertContains(res_staff, "Autonomic Vehicles")
        self.assertContains(res_staff, "Overdue Flagged")

    def test_command_output(self):
        out = StringIO()
        call_command('check_milestone_risk', stdout=out)
        self.assertIn("Checked", out.getvalue())
        self.assertIn("milestones:", out.getvalue())
