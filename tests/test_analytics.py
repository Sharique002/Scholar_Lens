from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.utils import timezone

from researchers.models import Department, ResearcherProfile
from papers.models import ResearchPaper, PaperAuthor
from funding.models import FundingCall, FundingApplication
from facilities.models import Facility, Booking


class AnalyticsReportTests(TestCase):
    def setUp(self):
        self.dept_cs = Department.objects.create(name='Computer Science', code='CS')
        self.dept_ee = Department.objects.create(name='Electrical Engineering', code='EE')

        # Dean user
        self.dean_user = User.objects.create_user(username='dean_jones', password='Password123!', email='dean@uni.edu')
        dean_group, _ = Group.objects.get_or_create(name='Dean of Research')
        self.dean_user.groups.add(dean_group)

        # Staff user (not Dean)
        self.staff_user = User.objects.create_user(username='staff_patel', password='Password123!', is_staff=True)

        # Faculty user
        self.faculty_user = User.objects.create_user(username='dr_watson', password='Password123!')
        self.faculty_profile = ResearcherProfile.objects.create(
            user=self.faculty_user,
            department=self.dept_cs,
            verification_status='VERIFIED'
        )

        # Academic Year: 2025-2026 (2025-07-01 to 2026-06-30)
        # Publication in AY 2025-2026
        self.paper = ResearchPaper.objects.create(
            title='Next-Gen Neural Networks',
            year=2025,
            publication_date=date(2025, 9, 15),
            status='PROCESSED',
            uploader=self.faculty_user
        )
        PaperAuthor.objects.create(paper=self.paper, name='Dr Watson', researcher=self.faculty_profile, order=1)

        # Funding application in AY 2025-2026
        self.call = FundingCall.objects.create(
            title='AI Grand Challenge',
            sponsor='DST',
            description='National AI Challenge',
            eligibility='Faculty',
            deadline=timezone.make_aware(timezone.datetime(2025, 8, 1, 12, 0)),
            is_published=True
        )
        self.fund_app = FundingApplication.objects.create(
            call=self.call,
            applicant=self.faculty_user,
            title='Deep Vision Algorithms',
            amount_requested=2500000.00,
            amount_awarded=2000000.00,
            status='AWARDED',
            decision_date=date(2025, 11, 1)
        )

    def test_full_year_report_loads_aggregates(self):
        client = Client()
        client.login(username='staff_patel', password='Password123!')

        resp = client.get(reverse('analytics:research'), {'year': '2025-2026'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Computer Science')
        self.assertContains(resp, 'Departmental Productivity')

    def test_productivity_dean_only(self):
        """Per-researcher individual productivity metrics are visible only to Dean of Research."""
        client_staff = Client()
        client_staff.login(username='staff_patel', password='Password123!')
        resp_staff = client_staff.get(reverse('analytics:research'), {'year': '2025-2026'})
        self.assertEqual(resp_staff.status_code, 200)
        # Staff sees department aggregates, but does not see per-researcher individual breakdown table
        self.assertNotContains(resp_staff, 'Individual Researcher Productivity')
        self.assertNotContains(resp_staff, 'dr_watson')

        client_dean = Client()
        client_dean.login(username='dean_jones', password='Password123!')
        resp_dean = client_dean.get(reverse('analytics:research'), {'year': '2025-2026'})
        self.assertEqual(resp_dean.status_code, 200)
        # Dean sees individual breakdown
        self.assertContains(resp_dean, 'Individual Researcher Productivity')
        self.assertContains(resp_dean, 'dr_watson')

    def test_full_year_report_exports_csv(self):
        client_dean = Client()
        client_dean.login(username='dean_jones', password='Password123!')

        resp = client_dean.get(reverse('analytics:research'), {'year': '2025-2026', 'export': 'csv'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/csv')
        csv_text = resp.content.decode('utf-8')
        self.assertIn('Department,Publications,Funding Awarded', csv_text)
        self.assertIn('Computer Science', csv_text)
        # Dean export includes individual researcher section
        self.assertIn('Researcher,Department,Publications', csv_text)
        self.assertIn('dr_watson', csv_text)

    def test_non_dean_csv_export_redacts_researchers(self):
        client_staff = Client()
        client_staff.login(username='staff_patel', password='Password123!')

        resp = client_staff.get(reverse('analytics:research'), {'year': '2025-2026', 'export': 'csv'})
        self.assertEqual(resp.status_code, 200)
        csv_text = resp.content.decode('utf-8')
        self.assertIn('Computer Science', csv_text)
        # Researcher breakdown is omitted
        self.assertNotIn('dr_watson', csv_text)
