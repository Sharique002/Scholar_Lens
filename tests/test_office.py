from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group

from researchers.models import ResearcherProfile, Department
from papers.models import ResearchPaper, DuplicateCandidate, PaperAuthor
from projects.models import ResearchProject, Milestone
from facilities.models import Facility, Booking
from dashboard.models import AuditEntry


class ResearchOfficeHubTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='office_admin', password='Password123!', is_staff=True)
        self.dean = User.objects.create_user(username='dean_exec', password='Password123!')
        dean_grp, _ = Group.objects.get_or_create(name='Dean of Research')
        self.dean.groups.add(dean_grp)

        self.student = User.objects.create_user(username='student_sam', password='Password123!')

        self.dept = Department.objects.create(name='Computer Science', code='CS')
        self.profile = ResearcherProfile.objects.create(
            user=self.student,
            department=self.dept,
            verification_status='PENDING'
        )

        self.paper1 = ResearchPaper.objects.create(title='P1', uploader=self.student, status='PROCESSED')
        self.paper2 = ResearchPaper.objects.create(title='P2', uploader=self.student, status='PROCESSED')
        self.dup = DuplicateCandidate.objects.create(
            incoming_paper=self.paper1,
            existing_paper=self.paper2,
            similarity_score=88.5,
            status='PENDING'
        )

        AuditEntry.objects.create(
            actor=self.staff,
            action='profile_verified',
            target_type='researchers.researcherprofile',
            target_id=self.profile.pk,
            data={'note': 'Approved'}
        )

    def test_office_hub_loads_for_staff(self):
        client = Client()
        client.login(username='office_admin', password='Password123!')
        resp = client.get(reverse('dashboard:office'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Research Office Governance Hub')
        self.assertContains(resp, 'Profile Verifications')
        self.assertContains(resp, 'Duplicate Publications')
        self.assertContains(resp, 'profile_verified')

    def test_office_hub_loads_for_dean(self):
        client = Client()
        client.login(username='dean_exec', password='Password123!')
        resp = client.get(reverse('dashboard:office'))
        self.assertEqual(resp.status_code, 200)

    def test_office_hub_forbidden_for_regular_user(self):
        client = Client()
        client.login(username='student_sam', password='Password123!')
        resp = client.get(reverse('dashboard:office'))
        self.assertEqual(resp.status_code, 403)
