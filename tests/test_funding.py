"""Tests for M6 Funding Call Register."""
from io import StringIO
from datetime import timedelta, date
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.management import call_command
from funding.models import FundingCall, FundingAlert
from funding.alerts import send_due_alerts
from dashboard.models import ResearchActivity


class FundingRegisterTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user('student_user', password='password123')
        self.staff = User.objects.create_user('staff_user', password='password123', is_staff=True)
        now = timezone.now()

        # Open call (12 days)
        self.call_open = FundingCall.objects.create(
            title="AI Innovation Grant",
            sponsor="Dept of Science & Technology",
            description="Grants for AI research.",
            eligibility="Faculty and postdocs.",
            research_area="AI",
            amount="Up to 25 Lakhs",
            deadline=now + timedelta(days=12),
            is_published=True,
            created_by=self.staff
        )

        # Closing soon call (1 day)
        self.call_closing = FundingCall.objects.create(
            title="Robotics Seed Grant",
            sponsor="Robotics Society",
            description="Seed funding for autonomous systems.",
            eligibility="All researchers.",
            research_area="AI",
            amount="Up to 10 Lakhs",
            deadline=now + timedelta(days=1),
            is_published=True,
            created_by=self.staff
        )

        # Closes today (few hours)
        self.call_today = FundingCall.objects.create(
            title="Bioinformatics Equipment Fund",
            sponsor="Biotech Council",
            description="Hardware for genome pipelines.",
            eligibility="Lab leads.",
            research_area="BIO",
            amount="Up to 50 Lakhs",
            deadline=now + timedelta(hours=3),
            is_published=True,
            created_by=self.staff
        )

        # Closed call (past)
        self.call_closed = FundingCall.objects.create(
            title="Legacy Computing Grant",
            sponsor="Old Foundation",
            description="Past fund.",
            eligibility="Closed.",
            research_area="SE",
            amount="Up to 5 Lakhs",
            deadline=now - timedelta(days=2),
            is_published=True,
            created_by=self.staff
        )

        # Unpublished call (open, but hidden from non-staff)
        self.call_unpublished = FundingCall.objects.create(
            title="Draft Cyber Fund",
            sponsor="Cybersecurity Hub",
            description="Draft fund not yet released.",
            eligibility="Staff only.",
            research_area="SEC",
            amount="Up to 15 Lakhs",
            deadline=now + timedelta(days=30),
            is_published=False,
            created_by=self.staff
        )

    def test_list_shows_published_open_first(self):
        self.client.force_login(self.student)
        res = self.client.get(reverse('funding:list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "AI Innovation Grant")
        self.assertContains(res, "Robotics Seed Grant")
        self.assertContains(res, "Legacy Computing Grant")
        # Unpublished is hidden for student
        self.assertNotContains(res, "Draft Cyber Fund")

        # Staff can see unpublished calls
        self.client.force_login(self.staff)
        res_staff = self.client.get(reverse('funding:list'))
        self.assertContains(res_staff, "Draft Cyber Fund")

    def test_filter_by_area_and_state(self):
        self.client.force_login(self.student)
        # Filter by area=AI & state=closing (meaning CLOSING_SOON)
        res = self.client.get(reverse('funding:list') + '?area=AI&state=closing')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Robotics Seed Grant")
        self.assertNotContains(res, "Bioinformatics Equipment Fund")

    def test_countdown_text(self):
        self.client.force_login(self.student)
        # Check call_open (12 days left)
        res = self.client.get(reverse('funding:detail', args=[self.call_open.pk]))
        self.assertContains(res, "12 days left")

        # Check call_closing (1 day left)
        res1 = self.client.get(reverse('funding:detail', args=[self.call_closing.pk]))
        self.assertContains(res1, "1 day left")

        # Check call_today (0 days left -> Closes today)
        res0 = self.client.get(reverse('funding:detail', args=[self.call_today.pk]))
        self.assertContains(res0, "Closes today")

        # Check call_closed (closed)
        res_c = self.client.get(reverse('funding:detail', args=[self.call_closed.pk]))
        self.assertContains(res_c, "Closed")

    def test_only_staff_can_create_edit(self):
        self.client.force_login(self.student)
        create_res = self.client.get(reverse('funding:create'))
        self.assertEqual(create_res.status_code, 403)
        edit_res = self.client.get(reverse('funding:edit', args=[self.call_open.pk]))
        self.assertEqual(edit_res.status_code, 403)

        self.client.force_login(self.staff)
        create_res_staff = self.client.get(reverse('funding:create'))
        self.assertEqual(create_res_staff.status_code, 200)
        edit_res_staff = self.client.get(reverse('funding:edit', args=[self.call_open.pk]))
        self.assertEqual(edit_res_staff.status_code, 200)

    def test_watch_toggle(self):
        self.client.force_login(self.student)
        url = reverse('funding:watch', args=[self.call_open.pk])
        # First POST: watch
        res = self.client.post(url, follow=True)
        self.assertEqual(res.status_code, 200)
        messages_list = [m.message for m in res.context['messages']]
        self.assertIn("You'll get deadline reminders for this call.", messages_list)
        self.assertTrue(self.call_open.watchers.filter(pk=self.student.pk).exists())

        # Second POST: unwatch
        res2 = self.client.post(url, follow=True)
        self.assertEqual(res2.status_code, 200)
        messages_list2 = [m.message for m in res2.context['messages']]
        self.assertIn("Reminders turned off.", messages_list2)
        self.assertFalse(self.call_open.watchers.filter(pk=self.student.pk).exists())


@override_settings(FUNDING_ALERT_DAYS=[30, 14, 7, 1])
class FundingAlertsTests(TestCase):
    def setUp(self):
        self.watcher = User.objects.create_user('watcher_user', password='password123')
        self.non_watcher = User.objects.create_user('non_watcher', password='password123')
        self.staff = User.objects.create_user('alerts_staff', password='password123', is_staff=True)
        self.ref_date = date(2026, 11, 2)
        now = timezone.make_aware(timezone.datetime(2026, 11, 2, 10, 0))

        # A call with deadline exactly 14 days ahead of ref_date
        self.call_14 = FundingCall.objects.create(
            title="Biotech Quantum Leap",
            sponsor="Science Foundation",
            description="Quantum biology fund.",
            eligibility="All.",
            research_area="BIO",
            deadline=now + timedelta(days=14),
            is_published=True,
            created_by=self.staff
        )
        self.call_14.watchers.add(self.watcher)

    def test_alert_fires_at_threshold(self):
        # 14 days left triggers threshold 14
        count = send_due_alerts(today=self.ref_date)
        self.assertEqual(count, 1)

        # Check notification in dashboard
        self.assertTrue(ResearchActivity.objects.filter(
            user=self.watcher,
            activity_type='FUNDING'
        ).exists())

        self.client.force_login(self.watcher)
        res = self.client.get(reverse('dashboard:notifications'))
        self.assertContains(res, "Biotech Quantum Leap")

    def test_no_alert_between_thresholds(self):
        self.call_14.delete()
        # Call 30 days away, first day passes 30
        call = FundingCall.objects.create(
            title="Green Energy Fund",
            sponsor="Renewable Energy Agency",
            description="Solar tech.",
            eligibility="All.",
            deadline=timezone.make_aware(timezone.datetime(2026, 12, 2, 10, 0)),
            is_published=True,
            created_by=self.staff
        )
        call.watchers.add(self.watcher)

        # At 30 days left (2 Nov)
        c1 = send_due_alerts(today=date(2026, 11, 2))
        self.assertEqual(c1, 1)

        # At 20 days left (12 Nov) - threshold 14 has not arrived yet, and 30 already fired
        c2 = send_due_alerts(today=date(2026, 11, 12))
        # No new alert should fire for this call
        self.assertFalse(FundingAlert.objects.filter(call=call, user=self.watcher, days_before=14).exists())
        self.assertEqual(c2, 0)

    def test_alerts_idempotent(self):
        # Running twice on the same day fires alert only once
        c1 = send_due_alerts(today=self.ref_date)
        self.assertEqual(c1, 1)

        c2 = send_due_alerts(today=self.ref_date)
        self.assertEqual(c2, 0)

    def test_missed_day_catches_up(self):
        # A call with deadline 5 days ahead
        call_5 = FundingCall.objects.create(
            title="Urgent Climate Challenge",
            sponsor="UN Climate Hub",
            description="Climate models.",
            eligibility="All.",
            deadline=timezone.make_aware(timezone.datetime(2026, 11, 7, 10, 0)),
            is_published=True,
            created_by=self.staff
        )
        call_5.watchers.add(self.watcher)

        # Day 1: 5 days left. The 7-day threshold was missed, so target is 7.
        c1 = send_due_alerts(today=self.ref_date)
        self.assertEqual(c1, 2)  # call_14 (14d) + call_5 (7d target)
        self.assertTrue(FundingAlert.objects.filter(call=call_5, days_before=7).exists())

        # Day 5: 1 day left. Threshold 1 is triggered.
        c2 = send_due_alerts(today=date(2026, 11, 6))
        self.assertTrue(FundingAlert.objects.filter(call=call_5, days_before=1).exists())
        self.assertGreaterEqual(c2, 1)

    def test_non_watchers_and_closed_calls_skipped(self):
        # Non-watcher does not get notification
        send_due_alerts(today=self.ref_date)
        self.assertFalse(ResearchActivity.objects.filter(user=self.non_watcher).exists())

        # Closed call (yesterday) gives 0 alerts
        call_closed = FundingCall.objects.create(
            title="Expired Call",
            sponsor="Old Agency",
            description="Expired.",
            eligibility="All.",
            deadline=timezone.make_aware(timezone.datetime(2026, 11, 1, 10, 0)),
            is_published=True,
            created_by=self.staff
        )
        call_closed.watchers.add(self.watcher)
        count = send_due_alerts(today=self.ref_date)
        self.assertEqual(count, 0)

    def test_command_output(self):
        out = StringIO()
        call_command('send_funding_alerts', stdout=out)
        self.assertIn("Sent", out.getvalue())
        self.assertIn("funding alerts.", out.getvalue())


class FundingApplicationTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('fund_staff', password='Password123!', is_staff=True)
        self.researcher = User.objects.create_user('res_dr', password='Password123!')
        self.call = FundingCall.objects.create(
            title='National Robotics Grant',
            sponsor='DST',
            description='Robotics R&D.',
            eligibility='Faculty',
            deadline=timezone.now() + timedelta(days=20),
            is_published=True,
            created_by=self.staff
        )

    def test_submit_funding_application(self):
        from funding.models import FundingApplication
        self.client.login(username='res_dr', password='Password123!')
        url = reverse('funding:apply', args=[self.call.pk])
        resp = self.client.post(url, {
            'title': 'Autonomous Navigation in Dense Crowds',
            'amount_requested': '1500000.00',
            'notes': 'Joint proposal with CS department.',
        })
        self.assertEqual(resp.status_code, 302)

        app = FundingApplication.objects.filter(call=self.call, applicant=self.researcher).first()
        self.assertIsNotNone(app)
        self.assertEqual(app.status, 'SUBMITTED')
        self.assertEqual(float(app.amount_requested), 1500000.00)

    def test_staff_record_award_decision_and_audit(self):
        from funding.models import FundingApplication
        from dashboard.models import AuditEntry
        app = FundingApplication.objects.create(
            call=self.call,
            applicant=self.researcher,
            title='Autonomous Navigation',
            amount_requested=1500000.00,
            status='SUBMITTED'
        )

        self.client.login(username='fund_staff', password='Password123!')
        url = reverse('funding:application_decision', args=[app.pk])
        resp = self.client.post(url, {
            'status': 'AWARDED',
            'amount_awarded': '1200000.00',
            'notes': 'Approved with slight reduction in travel budget.',
        })
        self.assertEqual(resp.status_code, 302)

        app.refresh_from_db()
        self.assertEqual(app.status, 'AWARDED')
        self.assertEqual(float(app.amount_awarded), 1200000.00)

        audit = AuditEntry.objects.filter(action='funding_decision', target_id=app.pk).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.actor, self.staff)

    def test_unauthorized_user_cannot_record_award_decision(self):
        from funding.models import FundingApplication
        app = FundingApplication.objects.create(
            call=self.call,
            applicant=self.researcher,
            title='Autonomous Navigation',
            amount_requested=1500000.00,
            status='SUBMITTED'
        )

        self.client.login(username='res_dr', password='Password123!')
        url = reverse('funding:application_decision', args=[app.pk])
        resp = self.client.post(url, {
            'status': 'AWARDED',
            'amount_awarded': '1200000.00',
        })
        self.assertEqual(resp.status_code, 403)
        app.refresh_from_db()
        self.assertEqual(app.status, 'SUBMITTED')


