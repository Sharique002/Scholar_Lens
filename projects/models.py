from django.db import models
from django.contrib.auth.models import User

class ResearchProject(models.Model):
    STATUS_CHOICES = (
        ('PLANNING', 'Planning'),
        ('ACTIVE', 'Active'),
        ('ON_HOLD', 'On Hold'),
        ('COMPLETED', 'Completed'),
        ('ARCHIVED', 'Archived'),
    )
    
    RESEARCH_AREA_CHOICES = [
        ('AI', 'Artificial Intelligence'),
        ('ML', 'Machine Learning'),
        ('DS', 'Data Science'),
        ('SE', 'Software Engineering'),
        ('HCI', 'Human-Computer Interaction'),
        ('BIO', 'Bioinformatics'),
        ('SEC', 'Cybersecurity'),
        ('NET', 'Networking'),
        ('OTHER', 'Other'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='led_projects')
    research_area = models.CharField(max_length=100, choices=RESEARCH_AREA_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNING')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['status']),
            models.Index(fields=['research_area']),
        ]

    def __str__(self):
        return self.title

class ProjectMember(models.Model):
    ROLE_CHOICES = (
        ('LEADER', 'Leader'),
        ('RESEARCHER', 'Researcher'),
        ('CONTRIBUTOR', 'Contributor'),
        ('REVIEWER', 'Reviewer'),
    )
    
    project = models.ForeignKey(ResearchProject, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='RESEARCHER')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['project', 'user']

    def __str__(self):
        return f"{self.user.username} - {self.project.title}"


class Milestone(models.Model):
    STATUS_CHOICES = (
        ('PLANNED', 'Planned'),
        ('IN_PROGRESS', 'In Progress'),
        ('DONE', 'Done'),
    )
    RISK_CHOICES = (
        ('ON_TRACK', 'On Track'),
        ('AT_RISK', 'At Risk'),
        ('OVERDUE', 'Overdue'),
    )

    project = models.ForeignKey(ResearchProject, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    is_deliverable = models.BooleanField(default=False)
    owner = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='owned_milestones'
    )
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    progress = models.PositiveSmallIntegerField(default=0)
    completed_on = models.DateField(null=True, blank=True)
    depends_on = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='blocks')
    risk = models.CharField(max_length=20, choices=RISK_CHOICES, default='ON_TRACK')
    risk_reason = models.CharField(max_length=200, blank=True)
    risk_checked_at = models.DateTimeField(null=True, blank=True)
    due_notified = models.BooleanField(default=False)

    class Meta:
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['risk', 'due_date']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(progress__lte=100),
                name='progress_lte_100'
            ),
        ]

    def __str__(self):
        return f"{self.project.title}: {self.title}"

    def save(self, *args, **kwargs):
        if self.status == 'DONE':
            self.progress = 100
            if not self.completed_on:
                from django.utils import timezone
                self.completed_on = timezone.localdate()
            self.risk = 'ON_TRACK'
            self.risk_reason = ''
        super().save(*args, **kwargs)

