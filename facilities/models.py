from django.db import models
from django.conf import settings
from django.db.models import Q, F
from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators
from django.contrib.postgres.constraints import ExclusionConstraint


class Facility(models.Model):
    KIND_CHOICES = (
        ('LAB', 'Laboratory'),
        ('EQUIPMENT', 'Specialized Equipment'),
        ('ROOM', 'Seminar / Meeting Room'),
        ('COMPUTE', 'Compute Cluster / GPU Server'),
    )

    name = models.CharField(max_length=200, unique=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    department = models.CharField(max_length=120)
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(default=1)
    custodian = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='custodian_facilities'
    )
    requires_approval = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'facilities'

    def can_manage(self, user):
        return bool(user and user.is_authenticated and (user.is_staff or user == self.custodian))

    def __str__(self):
        return self.name


class FacilitySlot(models.Model):
    WEEKDAY_CHOICES = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='slots')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    opens = models.TimeField()
    closes = models.TimeField()

    class Meta:
        ordering = ['facility', 'weekday', 'opens']
        constraints = [
            models.CheckConstraint(
                check=Q(closes__gt=F('opens')),
                name='slot_closes_after_opens'
            )
        ]

    def __str__(self):
        return f"{self.facility.name} - {self.get_weekday_display()} ({self.opens.strftime('%H:%M')}-{self.closes.strftime('%H:%M')})"


class Booking(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('NO_SHOW', 'No Show'),
    )

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='facility_bookings'
    )
    during = DateTimeRangeField()
    purpose = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            ExclusionConstraint(
                name='no_overlapping_active_bookings',
                expressions=[
                    ('facility', RangeOperators.EQUAL),
                    ('during', RangeOperators.OVERLAPS),
                ],
                condition=Q(status__in=['PENDING', 'APPROVED']),
            ),
        ]

    @property
    def start(self):
        return self.during.lower if self.during else None

    @property
    def end(self):
        return self.during.upper if self.during else None

    @property
    def hours(self):
        if self.during and self.during.lower and self.during.upper:
            return (self.during.upper - self.during.lower).total_seconds() / 3600.0
        return 0.0

    def __str__(self):
        return f"Booking #{self.pk} - {self.facility.name} ({self.status})"
