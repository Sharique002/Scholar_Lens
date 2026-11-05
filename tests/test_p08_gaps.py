"""Tests for the JSON API, opening/suggestion notifications, Scopus parsing and booking calendar export."""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from psycopg2.extras import DateTimeTZRange

from collaboration.suggestions import compute_suggestions
from dashboard.models import ResearchActivity
from facilities.models import Booking, Facility
from opportunities.models import ResearchOpening
from papers.importers import to_record
from researchers.models import ResearcherProfile, ResearchInterest, Skill


class ApiTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='api_user', password='Password123!')
        self.staff = User.objects.create_user(username='office', password='Password123!', is_staff=True)

    def test_requires_authentication(self):
        resp = self.client.get(reverse('api_researchers'))
        self.assertEqual(resp.status_code, 401)

    def test_list_endpoints_return_json(self):
        self.client.force_login(self.user)
        for name in ('api_researchers', 'api_publications', 'api_openings', 'api_projects',
                     'api_facilities', 'api_bookings', 'api_funding_calls'):
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 200, name)
            self.assertIn('results', resp.json())

    def test_expertise_search_requires_query(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('api_search_expertise')).status_code, 400)

    def test_analytics_restricted_to_office_and_dean(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('api_analytics_research')).status_code, 403)
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('api_analytics_research'))
        self.assertEqual(resp.status_code, 200)
        # Staff who are not the Dean must not see per-researcher productivity.
        self.assertFalse(resp.json()['researcher_metrics'])


class NotificationTest(TestCase):
    def setUp(self):
        self.faculty = User.objects.create_user(username='prof', password='Password123!')
        self.student = User.objects.create_user(username='student', password='Password123!')
        self.unrelated = User.objects.create_user(username='unrelated', password='Password123!')
        self.skill = Skill.objects.create(name='PyTorch')
        p, _ = ResearcherProfile.objects.get_or_create(user=self.student)
        p.skills.add(self.skill)
        ResearcherProfile.objects.get_or_create(user=self.unrelated)

    def test_new_opening_notifies_matching_researchers_only(self):
        self.client.force_login(self.faculty)
        self.client.post(reverse('opportunities:create'), {
            'title': 'RA in Deep Learning',
            'description': 'Train models.',
            'required_skills': [self.skill.pk],
            'spots_available': 1,
            'status': 'OPEN',
        })
        self.assertTrue(ResearchOpening.objects.filter(title='RA in Deep Learning').exists())
        notified = set(ResearchActivity.objects.filter(activity_type='OPENING').values_list('user__username', flat=True))
        self.assertEqual(notified, {'student'})

    def test_suggestion_notifies_once(self):
        interest = ResearchInterest.objects.create(name='Machine Learning')
        a, _ = ResearcherProfile.objects.get_or_create(user=self.faculty)
        b, _ = ResearcherProfile.objects.get_or_create(user=self.student)
        a.interests.add(interest)
        b.interests.add(interest)
        notes = ResearchActivity.objects.filter(user=self.faculty, activity_type='SUGGESTION')
        compute_suggestions(target_researcher=a)
        first = notes.count()
        self.assertGreaterEqual(first, 1)
        compute_suggestions(target_researcher=a)
        self.assertEqual(notes.count(), first)  # recompute must not re-notify


class ScopusRecordTest(TestCase):
    def test_parses_valid_entry(self):
        rec = to_record({
            'dc:title': 'Graph Learning at Scale',
            'prism:publicationName': 'Journal of ML',
            'prism:doi': '10.1000/ABC',
            'prism:coverDate': '2024-05-01',
            'subtypeDescription': 'Conference Paper',
            'dc:creator': 'Sharma A.',
            'eid': '2-s2.0-123',
        }, 'SCOPUS')
        self.assertEqual(rec['doi'], '10.1000/abc')
        self.assertEqual(rec['year'], 2024)
        self.assertEqual(rec['pub_type'], 'CONFERENCE')
        self.assertEqual(rec['authors'], [{'name': 'Sharma A.', 'orcid': None}])

    def test_malformed_entries_skipped(self):
        for bad in (None, 'string', {}, {'dc:title': '   '}, {'dc:title': None}):
            self.assertIsNone(to_record(bad, 'SCOPUS'))


class BookingIcsTest(TestCase):
    def setUp(self):
        self.custodian = User.objects.create_user(username='cust', password='Password123!')
        self.owner = User.objects.create_user(username='owner', password='Password123!')
        self.other = User.objects.create_user(username='other', password='Password123!')
        facility = Facility.objects.create(
            name='Electron Microscope', kind='EQUIPMENT', department='Physics',
            location='Lab 2, Block A', custodian=self.custodian,
        )
        start = timezone.now() + timedelta(days=2)
        self.booking = Booking.objects.create(
            facility=facility, user=self.owner, purpose='Imaging; samples, batch 1',
            during=DateTimeTZRange(start, start + timedelta(hours=2)), status='APPROVED',
        )

    def test_owner_gets_ics(self):
        self.client.force_login(self.owner)
        resp = self.client.get(reverse('facilities:booking_ics', args=[self.booking.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp['Content-Type'].startswith('text/calendar'))
        body = resp.content.decode()
        self.assertIn('BEGIN:VEVENT', body)
        self.assertIn('DESCRIPTION:Imaging\\; samples\\, batch 1', body)

    def test_other_user_forbidden_and_pending_not_exported(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('facilities:booking_ics', args=[self.booking.pk])).status_code, 403)
        self.booking.status = 'PENDING'
        self.booking.save()
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse('facilities:booking_ics', args=[self.booking.pk])).status_code, 403)
