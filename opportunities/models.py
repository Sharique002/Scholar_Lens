from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_cv_pdf(file):
    if not file.name.lower().endswith('.pdf'):
        raise ValidationError(_("Only PDF files are allowed."))
    if file.size > 5 * 1024 * 1024:
        raise ValidationError(_("File size must not exceed 5 MB."))


class ResearchOpening(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', _('Open')
        CLOSED = 'CLOSED', _('Closed')

    project = models.ForeignKey(
        'projects.ResearchProject',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='openings'
    )
    department = models.ForeignKey(
        'researchers.Department',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='openings'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    required_skills = models.ManyToManyField(
        'researchers.Skill',
        blank=True,
        related_name='openings'
    )
    spots_available = models.PositiveIntegerField(default=1)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_openings'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return self.title


class OpportunityApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        SHORTLISTED = 'SHORTLISTED', _('Shortlisted')
        ACCEPTED = 'ACCEPTED', _('Accepted')
        REJECTED = 'REJECTED', _('Rejected')

    opening = models.ForeignKey(
        ResearchOpening,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='opportunity_applications'
    )
    statement = models.TextField(help_text=_("Statement of interest or suitability."))
    cv_pdf = models.FileField(
        upload_to='opportunity_cvs/',
        validators=[validate_cv_pdf],
        help_text=_("Applicant CV/Resume (PDF only, max 5MB).")
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('opening', 'applicant')
        indexes = [
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"Application by {self.applicant.username} for {self.opening.title}"
