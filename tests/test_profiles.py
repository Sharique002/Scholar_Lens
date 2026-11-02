"""Tests for M1 Researcher Profiles, Departments, Verification, and Audit."""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from researchers.models import ResearcherProfile, Department, ResearchInterest
from dashboard.models import ResearchActivity, AuditEntry


class ProfileVerificationTests(TestCase):
    def setUp(self):
        self.staff1 = User.objects.create_user('staff1', password='password123', is_staff=True, first_name='Staff', last_name='One')
        self.staff2 = User.objects.create_user('staff2', password='password123', is_staff=True, first_name='Staff', last_name='Two')
        self.researcher = User.objects.create_user('dr_smith', password='password123', first_name='John', last_name='Smith')
        self.student = User.objects.create_user('student_user', password='password123')

        self.dept_cse = Department.objects.create(name='Computer Science and Engineering', code='CSE')
        self.dept_bio = Department.objects.create(name='Biotechnology', code='BIO')

        self.profile = ResearcherProfile.objects.create(
            user=self.researcher,
            department=self.dept_cse,
            orcid_id='0000-0002-1825-0097'
        )

    def test_request_verification(self):
        self.client.force_login(self.researcher)
        url = reverse('researchers:request_verification')
        res = self.client.post(url, follow=True)
        self.assertEqual(res.status_code, 200)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, 'PENDING')

        # Check every staff user gets a notification
        staff1_notifs = ResearchActivity.objects.filter(user=self.staff1, activity_type='VERIFICATION')
        staff2_notifs = ResearchActivity.objects.filter(user=self.staff2, activity_type='VERIFICATION')
        self.assertTrue(staff1_notifs.exists())
        self.assertTrue(staff2_notifs.exists())
        self.assertIn("asked to verify their profile", staff1_notifs.first().description)

        # Profile detail page shows badge "Verification pending"
        detail_res = self.client.get(reverse('researchers:detail', args=[self.profile.pk]))
        self.assertContains(detail_res, "Verification pending")

    def test_only_office_can_verify(self):
        self.profile.verification_status = 'PENDING'
        self.profile.save()

        self.client.force_login(self.student)
        url = reverse('researchers:verify', args=[self.profile.pk])
        res = self.client.post(url, {'action': 'approve'})
        self.assertEqual(res.status_code, 403)

        queue_res = self.client.get(reverse('researchers:verification_queue'))
        self.assertEqual(queue_res.status_code, 403)

    def test_verify_approve_reject_audited(self):
        # 1. Approve
        self.profile.verification_status = 'PENDING'
        self.profile.save()

        self.client.force_login(self.staff1)
        url = reverse('researchers:verify', args=[self.profile.pk])
        res = self.client.post(url, {'action': 'approve'}, follow=True)
        self.assertEqual(res.status_code, 200)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, 'VERIFIED')
        self.assertEqual(self.profile.verified_by, self.staff1)
        self.assertIsNotNone(self.profile.verified_at)

        # Audit entry check
        audit = AuditEntry.objects.filter(target_type='researchers.researcherprofile', target_id=self.profile.pk, action='profile.verified')
        self.assertTrue(audit.exists())
        self.assertEqual(audit.first().actor, self.staff1)

        # Notification to researcher
        self.assertTrue(ResearchActivity.objects.filter(user=self.researcher, activity_type='VERIFICATION').exists())

        # 2. Reject
        self.profile.verification_status = 'PENDING'
        self.profile.save()

        res_rej = self.client.post(url, {'action': 'reject', 'note': 'ORCID profile not public'}, follow=True)
        self.assertEqual(res_rej.status_code, 200)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, 'REJECTED')
        self.assertEqual(self.profile.verification_note, 'ORCID profile not public')

        audit_rej = AuditEntry.objects.filter(target_type='researchers.researcherprofile', target_id=self.profile.pk, action='profile.rejected')
        self.assertTrue(audit_rej.exists())

        # Notification mentions the note
        notif = ResearchActivity.objects.filter(user=self.researcher, activity_type='VERIFICATION').latest('created_at')
        self.assertIn('ORCID profile not public', notif.description)

    def test_editing_core_fields_resets_verification(self):
        self.profile.verification_status = 'VERIFIED'
        self.profile.verified_by = self.staff1
        self.profile.save()

        self.client.force_login(self.researcher)
        url = reverse('researchers:edit_profile')

        # Change department
        post_data = {
            'headline': 'Updated headline',
            'department': self.dept_bio.pk,
            'orcid_id': '0000-0002-1825-0097',
            'expertise_summary': 'Summary',
            'years_experience': 5,
        }
        res = self.client.post(url, post_data, follow=True)
        self.assertEqual(res.status_code, 200)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, 'UNVERIFIED')
        messages_list = [m.message for m in res.context['messages']]
        self.assertTrue(any("Your profile changed, so please request verification again." in m for m in messages_list))

    def test_orcid_format_validated(self):
        self.client.force_login(self.researcher)
        url = reverse('researchers:edit_profile')

        # Invalid format: 1234
        res1 = self.client.post(url, {'orcid_id': '1234', 'department': self.dept_cse.pk})
        self.assertContains(res1, "Enter a valid ORCID iD, like 0000-0002-1825-0097.")

        # Invalid checksum: 0000-0002-1825-0098
        res2 = self.client.post(url, {'orcid_id': '0000-0002-1825-0098', 'department': self.dept_cse.pk})
        self.assertContains(res2, "Enter a valid ORCID iD, like 0000-0002-1825-0097.")

        # Valid checksum: 0000-0002-1825-0097
        res3 = self.client.post(url, {'orcid_id': '0000-0002-1825-0097', 'department': self.dept_cse.pk})
        self.assertNotContains(res3, "Enter a valid ORCID iD")

    def test_verified_badge_on_detail_and_list(self):
        self.profile.verification_status = 'VERIFIED'
        self.profile.save()

        self.client.force_login(self.researcher)

        # Detail page
        res_detail = self.client.get(reverse('researchers:detail', args=[self.profile.pk]))
        self.assertContains(res_detail, "Verified")

        # List page
        res_list = self.client.get(reverse('researchers:list'))
        self.assertContains(res_list, "Verified")
