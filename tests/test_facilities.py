from datetime import datetime, time, timedelta, date
from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from psycopg2.extras import DateTimeTZRange

from facilities.models import Facility, FacilitySlot, Booking


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
        # Create slots for active lab (Monday 09:00 - 17:00)
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
        # Use next Monday
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
        # Valid week
        r = self.client.get(reverse('facilities:detail', args=[self.active_lab.pk]), {'week': '2026-11-02'})
        self.assertEqual(r.status_code, 200)
        # Bad week fallback without 500
        r_bad = self.client.get(reverse('facilities:detail', args=[self.active_lab.pk]), {'week': 'not-a-date'})
        self.assertEqual(r_bad.status_code, 200)
