from django.db import models
from django.conf import settings
from django.utils import timezone
from projects.models import ResearchProject


class FundingCall(models.Model):
    title = models.CharField(max_length=255)
    sponsor = models.CharField(max_length=200)
    description = models.TextField()
    eligibility = models.TextField()
    research_area = models.CharField(
        max_length=100,
        choices=ResearchProject.RESEARCH_AREA_CHOICES,
        blank=True
    )
    amount = models.CharField(
        max_length=100,
        blank=True,
        help_text='Free text funding amount, e.g. "Up to ₹25 lakh"'
    )
    url = models.URLField(blank=True)
    opens_on = models.DateField(null=True, blank=True)
    deadline = models.DateTimeField()
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_funding_calls'
    )
    watchers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='watched_funding_calls'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['deadline']
        indexes = [
            models.Index(fields=['deadline']),
        ]

    def __str__(self):
        return f"{self.title} ({self.sponsor})"

    def days_left(self, today=None) -> int:
        if today is None:
            today = timezone.localdate()
        deadline_date = timezone.localtime(self.deadline).date() if timezone.is_aware(self.deadline) else self.deadline.date()
        return (deadline_date - today).days

    def state(self, today=None) -> str:
        left = self.days_left(today)
        if left < 0:
            return 'CLOSED'
        if left <= 14:
            return 'CLOSING_SOON'
        return 'OPEN'
    
    @property
    def countdown_label(self) -> str:
        left = self.days_left()
        if left < 0:
            return 'Closed'
        if left == 0:
            return 'Closes today'
        if left == 1:
            return '1 day left'
        return f"{left} days left"


class FundingAlert(models.Model):
    call = models.ForeignKey(
        FundingCall,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='funding_alerts'
    )
    days_before = models.PositiveSmallIntegerField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('call', 'user', 'days_before')

    def __str__(self):
        return f"Alert for {self.user.username} on {self.call.title} ({self.days_before}d)"
