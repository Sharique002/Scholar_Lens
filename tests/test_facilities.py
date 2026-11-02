from datetime import datetime, time, timedelta, date
import threading
from unittest import skipUnless

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction, connection
from django.urls import reverse
from django.utils import timezone
from psycopg2.extras import DateTimeTZRange

from facilities.models import Facility, FacilitySlot, Booking
from facilities.forms import BookingForm
from facilities.views import create_booking


class FacilitiesModelTest(TestCase):
    def setUp(self):
        self.custodian = User.objects.create_user(
            username='custodian1',
            password='Password123!',
            email='custodian@example.com'
        )
        self.user1 = User.objects.create_user(
            username='researcher1',
            password='Password123!',
            email='r1@example.com'
        )
        self.user2 = User.objects.create_user(
            username='researcher2',
            password='Password123!',
            email='r2@example.com'
        )
        self.facility = Facility.objects.create(
            name='High Performance GPU Cluster',
            kind='COMPUTE',
            department='Computer Science',
            location='Tech Tower 401',
            description='8x NVIDIA H100 GPUs for deep learning workloads',
            capacity=4,
            custodian=self.custodian,
            requires_approval=True
        )
        self.slot = FacilitySlot.objects.create(
            facility=self.facility,
            weekday=0,  # Monday
            opens=time(9, 0),
            closes=time(18, 0)
        )

    def test_models_create_and_str(self):
        self.assertEqual(str(self.facility), 'High Performance GPU Cluster')
        self.assertIn('Monday', str(self.slot))
        self.assertTrue(self.facility.can_manage(self.custodian))
        self.assertFalse(self.facility.can_manage(self.user1))

        base_dt = timezone.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
        start = base_dt
        end = base_dt + timedelta(hours=2)
        booking = Booking.objects.create(
            facility=self.facility,
            user=self.user1,
            during=DateTimeTZRange(start, end, bounds='[)'),
            purpose='LLM fine-tuning experiment'
        )
        self.assertIn('Booking #', str(booking))
        self.assertEqual(booking.start, start)
        self.assertEqual(booking.end, end)
        self.assertEqual(booking.hours, 2.0)

    def test_partial_overlap_rejected(self):
        base_dt = timezone.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=2)
        # 10:00 to 11:00
        Booking.objects.create(
            facility=self.facility,
            user=self.user1,
            during=DateTimeTZRange(base_dt + timedelta(hours=10), base_dt + timedelta(hours=11), bounds='[)'),
            purpose='Slot A',
            status='PENDING'
        )
        # 10:30 to 11:30 - overlapping!
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Booking.objects.create(
                    facility=self.facility,
                    user=self.user2,
                    during=DateTimeTZRange(base_dt + timedelta(hours=10, minutes=30), base_dt + timedelta(hours=11, minutes=30), bounds='[)'),
                    purpose='Slot B Overlap',
                    status='PENDING'
                )

    def test_back_to_back_allowed(self):
        base_dt = timezone.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=3)
        b1 = Booking.objects.create(
            facility=self.facility,
            user=self.user1,
            during=DateTimeTZRange(base_dt + timedelta(hours=10), base_dt + timedelta(hours=11), bounds='[)'),
            purpose='Slot 10-11',
            status='PENDING'
        )
        b2 = Booking.objects.create(
            facility=self.facility,
            user=self.user2,
            during=DateTimeTZRange(base_dt + timedelta(hours=11), base_dt + timedelta(hours=12), bounds='[)'),
            purpose='Slot 11-12',
            status='PENDING'
        )
        self.assertIsNotNone(b1.pk)
        self.assertIsNotNone(b2.pk)

    def test_rejected_booking_frees_slot(self):
        base_dt = timezone.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=4)
        b1 = Booking.objects.create(
            facility=self.facility,
            user=self.user1,
            during=DateTimeTZRange(base_dt + timedelta(hours=14), base_dt + timedelta(hours=16), bounds='[)'),
            purpose='First attempt',
            status='REJECTED'
        )
        b2 = Booking.objects.create(
            facility=self.facility,
            user=self.user2,
            during=DateTimeTZRange(base_dt + timedelta(hours=14), base_dt + timedelta(hours=16), bounds='[)'),
            purpose='Second attempt for same time',
            status='PENDING'
        )
        self.assertIsNotNone(b2.pk)

    def test_other_facility_same_time_allowed(self):
        other_facility = Facility.objects.create(
            name='Confocal Microscope Suite',
            kind='EQUIPMENT',
            department='Biotechnology',
            location='Bio Science 102',
            capacity=1,
            custodian=self.custodian
        )
        base_dt = timezone.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=5)
        b1 = Booking.objects.create(
            facility=self.facility,
            user=self.user1,
            during=DateTimeTZRange(base_dt + timedelta(hours=9), base_dt + timedelta(hours=11), bounds='[)'),
            purpose='GPU run',
            status='APPROVED'
        )
        b2 = Booking.objects.create(
            facility=other_facility,
            user=self.user2,
            during=DateTimeTZRange(base_dt + timedelta(hours=9), base_dt + timedelta(hours=11), bounds='[)'),
            purpose='Imaging run',
            status='APPROVED'
        )
        self.assertIsNotNone(b1.pk)
        self.assertIsNotNone(b2.pk)


class FacilityViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='fac_user',
            password='Password123!',
            email='fac_user@example.com'
        )
        self.custodian = User.objects.create_user(
            username='custodian2',
            password='Password123!',
            email='custodian2@example.com'
        )
        self.active_lab = Facility.objects.create(
            name='Advanced Robotics Laboratory',
            kind='LAB',
            department='CSE',
            location='Block 34, Room 101',
            custodian=self.custodian,
            is_active=True
        )
        self.inactive_facility = Facility.objects.create(
            name='Decommissioned Server Room',
            kind='ROOM',
            department='CSE',
            location='Basement',
            custodian=self.custodian,
            is_active=False
        )
        self.biotech_equip = Facility.objects.create(
            name='Mass Spectrometer Core',
            kind='EQUIPMENT',
            department='Biotech',
            location='Block 28, Lab 3',
            custodian=self.custodian,
            is_active=True
        )
        FacilitySlot.objects.create(
            facility=self.active_lab,
            weekday=0,
            opens=time(9, 0),
            closes=time(17, 0)
        )

    def test_list_shows_active_only(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse('facilities:list'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Advanced Robotics Laboratory')
        self.assertNotContains(r, 'Decommissioned Server Room')

    def test_list_filters_by_kind_and_department(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse('facilities:list'), {'kind': 'LAB', 'department': 'CSE'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Advanced Robotics Laboratory')
        self.assertNotContains(r, 'Mass Spectrometer Core')

    def test_detail_shows_week_calendar(self):
        self.client.force_login(self.user)
        today = timezone.localdate()
        days_ahead = (0 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        target_monday = today + timedelta(days=days_ahead)
        start_dt = timezone.make_aware(datetime.combine(target_monday, time(10, 0)))
        end_dt = timezone.make_aware(datetime.combine(target_monday, time(12, 0)))

        Booking.objects.create(
            facility=self.active_lab,
            user=self.user,
            during=DateTimeTZRange(start_dt, end_dt, bounds='[)'),
            purpose='Autonomous Rover Calibration',
            status='APPROVED'
        )
        Booking.objects.create(
            facility=self.active_lab,
            user=self.user,
            during=DateTimeTZRange(start_dt + timedelta(hours=2), end_dt + timedelta(hours=2), bounds='[)'),
            purpose='Secret Cancelled Meeting',
            status='REJECTED'
        )

        r = self.client.get(reverse('facilities:detail', args=[self.active_lab.pk]), {'week': target_monday.strftime('%Y-%m-%d')})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '09:00')
        self.assertContains(r, '17:00')
        self.assertContains(r, 'Autonomous Rover Calibration')
        self.assertNotContains(r, 'Secret Cancelled Meeting')

    def test_detail_week_param(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse('facilities:detail', args=[self.active_lab.pk]), {'week': '2026-11-02'})
        self.assertEqual(r.status_code, 200)
        r_bad = self.client.get(reverse('facilities:detail', args=[self.active_lab.pk]), {'week': 'not-a-date'})
        self.assertEqual(r_bad.status_code, 200)


class BookingFormAndWorkflowTest(TestCase):
    def setUp(self):
        self.custodian = User.objects.create_user(
            username='custodian_wf',
            password='Password123!',
            email='cwf@example.com'
        )
        self.user = User.objects.create_user(
            username='booker_wf',
            password='Password123!',
            email='booker@example.com'
        )
        self.facility_approval = Facility.objects.create(
            name='Clean Room Fab',
            kind='LAB',
            department='ECE',
            location='Nano Center 101',
            custodian=self.custodian,
            requires_approval=True
        )
        self.facility_instant = Facility.objects.create(
            name='Open VR Studio',
            kind='ROOM',
            department='Media',
            location='Design Wing 204',
            custodian=self.custodian,
            requires_approval=False
        )
        for fac in [self.facility_approval, self.facility_instant]:
            for w in range(5):
                FacilitySlot.objects.create(
                    facility=fac,
                    weekday=w,
                    opens=time(8, 0),
                    closes=time(18, 0)
                )

    def test_booking_form_validation(self):
        today = timezone.localdate()
        days_ahead = (1 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        future_tuesday = today + timedelta(days=days_ahead)

        # 1. End <= start
        form1 = BookingForm(
            data={
                'date': future_tuesday.strftime('%Y-%m-%d'),
                'start_time': '12:00',
                'end_time': '11:00',
                'purpose': 'Invalid times'
            },
            facility=self.facility_approval
        )
        self.assertFalse(form1.is_valid())
        self.assertIn("End time must be after start time.", form1.non_field_errors())

        # 2. Start in the past
        past_date = today - timedelta(days=1)
        form2 = BookingForm(
            data={
                'date': past_date.strftime('%Y-%m-%d'),
                'start_time': '10:00',
                'end_time': '11:00',
                'purpose': 'Past booking'
            },
            facility=self.facility_approval
        )
        self.assertFalse(form2.is_valid())
        self.assertIn("You can't book a time in the past.", form2.non_field_errors())

        # 3. Longer than 8h
        form3 = BookingForm(
            data={
                'date': future_tuesday.strftime('%Y-%m-%d'),
                'start_time': '08:00',
                'end_time': '17:00',
                'purpose': 'Marathon session'
            },
            facility=self.facility_approval
        )
        self.assertFalse(form3.is_valid())
        self.assertIn("A single booking can be at most 8 hours.", form3.non_field_errors())

        # 4. Outside every slot that weekday
        form4 = BookingForm(
            data={
                'date': future_tuesday.strftime('%Y-%m-%d'),
                'start_time': '18:00',
                'end_time': '20:00',
                'purpose': 'Night work'
            },
            facility=self.facility_approval
        )
        self.assertFalse(form4.is_valid())
        self.assertTrue(any("The facility is closed at that time. Open hours:" in err for err in form4.non_field_errors()))

    def test_book_creates_pending_and_redirects(self):
        self.client.force_login(self.user)
        today = timezone.localdate()
        days_ahead = (2 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        future_wednesday = today + timedelta(days=days_ahead)

        # Facility with approval
        r1 = self.client.post(reverse('facilities:book', args=[self.facility_approval.pk]), {
            'date': future_wednesday.strftime('%Y-%m-%d'),
            'start_time': '10:00',
            'end_time': '12:00',
            'purpose': 'Semiconductor photolithography'
        }, follow=True)
        self.assertEqual(r1.status_code, 200)
        self.assertContains(r1, "Booking requested. The custodian will approve it soon.")
        b1 = Booking.objects.get(purpose='Semiconductor photolithography')
        self.assertEqual(b1.status, 'PENDING')

        # Facility without approval (instant)
        r2 = self.client.post(reverse('facilities:book', args=[self.facility_instant.pk]), {
            'date': future_wednesday.strftime('%Y-%m-%d'),
            'start_time': '14:00',
            'end_time': '16:00',
            'purpose': 'Virtual Reality Study'
        }, follow=True)
        self.assertEqual(r2.status_code, 200)
        self.assertContains(r2, "Booking confirmed.")
        b2 = Booking.objects.get(purpose='Virtual Reality Study')
        self.assertEqual(b2.status, 'APPROVED')

    def test_book_conflict_shows_friendly_error(self):
        self.client.force_login(self.user)
        today = timezone.localdate()
        days_ahead = (3 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        future_thursday = today + timedelta(days=days_ahead)
        start_dt = timezone.make_aware(datetime.combine(future_thursday, time(10, 0)))
        end_dt = timezone.make_aware(datetime.combine(future_thursday, time(12, 0)))

        Booking.objects.create(
            facility=self.facility_approval,
            user=self.custodian,
            during=DateTimeTZRange(start_dt, end_dt, bounds='[)'),
            purpose='Pre-existing booking',
            status='PENDING'
        )
        initial_count = Booking.objects.count()

        r = self.client.post(reverse('facilities:book', args=[self.facility_approval.pk]), {
            'date': future_thursday.strftime('%Y-%m-%d'),
            'start_time': '11:00',
            'end_time': '13:00',
            'purpose': 'Conflicting booking'
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "That time was just taken. Please pick another slot.")
        self.assertEqual(Booking.objects.count(), initial_count)


class ConcurrentBookingConcurrencyTest(TransactionTestCase):
    @skipUnless(connection.vendor == 'postgresql', 'PostgreSQL only')
    def test_concurrent_booking_only_one_wins(self):
        custodian = User.objects.create_user('cust_c', 'c@example.com', 'p')
        facility = Facility.objects.create(
            name='Concurrent Cluster',
            kind='COMPUTE',
            department='CS',
            location='Lab 1',
            custodian=custodian
        )
        users = [User.objects.create_user(f'thread_user_{i}', f'u{i}@example.com', 'p') for i in range(5)]

        base_dt = timezone.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=10)
        target_range = DateTimeTZRange(base_dt + timedelta(hours=10), base_dt + timedelta(hours=12), bounds='[)')

        barrier = threading.Barrier(5)
        results = []

        def worker(user):
            try:
                barrier.wait()
                b = create_booking(facility, user, target_range, f'Booking by {user.username}')
                results.append(b)
            finally:
                connection.close()

        threads = [threading.Thread(target=worker, args=(u,)) for u in users]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successes = [r for r in results if r is not None]
        conflicts = [r for r in results if r is None]

        self.assertEqual(len(successes), 1)
        self.assertEqual(len(conflicts), 4)
        self.assertEqual(Booking.objects.filter(facility=facility).count(), 1)
