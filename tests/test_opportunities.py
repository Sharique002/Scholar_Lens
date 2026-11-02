import io
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from researchers.models import Department, Skill
from dashboard.models import AuditEntry
from projects.models import ResearchProject, ProjectMember
from opportunities.models import ResearchOpening, OpportunityApplication


class ResearchOpportunitiesTest(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Computer Science', code='CS')
        self.faculty = User.objects.create_user(username='prof_clark', password='Password123!', email='clark@uni.edu')
        self.student = User.objects.create_user(username='john_doe', password='Password123!', email='john@uni.edu')
        self.other_user = User.objects.create_user(username='other_user', password='Password123!', email='other@uni.edu')

        self.project = ResearchProject.objects.create(
            title='Autonomous Drones Lab',
            description='Vision-based navigation.',
            leader=self.faculty,
            research_area='ROBOTICS'
        )

        self.skill_cv = Skill.objects.create(name='OpenCV')
        self.skill_ros = Skill.objects.create(name='ROS')

        self.opening = ResearchOpening.objects.create(
            project=self.project,
            department=self.dept,
            title='Graduate Research Assistant (Vision Navigation)',
            description='Work on real-time SLAM algorithms.',
            spots_available=2,
            deadline=timezone.now().date() + timezone.timedelta(days=30),
            status='OPEN',
            created_by=self.faculty
        )
        self.opening.required_skills.add(self.skill_cv, self.skill_ros)

    def test_openings_list_view(self):
        client = Client()
        client.login(username='john_doe', password='Password123!')
        resp = client.get(reverse('opportunities:list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Graduate Research Assistant')
        self.assertContains(resp, 'Autonomous Drones Lab')

    def test_submit_application_success(self):
        client = Client()
        client.login(username='john_doe', password='Password123!')
        pdf_content = b"%PDF-1.4 dummy valid pdf content for testing cv upload"
        pdf_file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")

        url = reverse('opportunities:apply', args=[self.opening.pk])
        resp = client.post(url, {
            'statement': 'I have worked extensively with OpenCV and ROS.',
            'cv_pdf': pdf_file,
        })
        self.assertEqual(resp.status_code, 302)

        app = OpportunityApplication.objects.filter(opening=self.opening, applicant=self.student).first()
        self.assertIsNotNone(app)
        self.assertEqual(app.status, 'PENDING')
        self.assertTrue(app.cv_pdf.name.endswith('.pdf'))

    def test_submit_application_rejects_non_pdf(self):
        client = Client()
        client.login(username='john_doe', password='Password123!')
        txt_file = SimpleUploadedFile("resume.txt", b"plain text is not allowed", content_type="text/plain")

        url = reverse('opportunities:apply', args=[self.opening.pk])
        resp = client.post(url, {
            'statement': 'Applying with text file',
            'cv_pdf': txt_file,
        })
        # Should stay on page with form errors
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(OpportunityApplication.objects.filter(opening=self.opening, applicant=self.student).exists())

    def test_review_application_accept_adds_member_and_logs_audit(self):
        app = OpportunityApplication.objects.create(
            opening=self.opening,
            applicant=self.student,
            statement='Strong CV in robotics.'
        )

        client = Client()
        client.login(username='prof_clark', password='Password123!')
        review_url = reverse('opportunities:review', args=[app.pk, 'accept'])
        resp = client.post(review_url)
        self.assertEqual(resp.status_code, 302)

        app.refresh_from_db()
        self.assertEqual(app.status, 'ACCEPTED')
        self.assertEqual(app.reviewed_by, self.faculty)

        # Verified added to project members
        is_member = ProjectMember.objects.filter(project=self.project, user=self.student).exists()
        self.assertTrue(is_member)

        # Audit entry recorded
        audit = AuditEntry.objects.filter(action='application_accepted', target_id=app.pk).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.actor, self.faculty)

    def test_unauthorized_user_cannot_review_application(self):
        app = OpportunityApplication.objects.create(
            opening=self.opening,
            applicant=self.student,
            statement='Strong CV in robotics.'
        )

        client = Client()
        client.login(username='other_user', password='Password123!')
        review_url = reverse('opportunities:review', args=[app.pk, 'accept'])
        resp = client.post(review_url)
        self.assertEqual(resp.status_code, 403)

        app.refresh_from_db()
        self.assertEqual(app.status, 'PENDING')
