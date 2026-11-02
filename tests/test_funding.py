"""Tests for M6 Funding Call Register."""
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from funding.models import FundingCall, FundingAlert


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
