from datetime import datetime, time, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
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
