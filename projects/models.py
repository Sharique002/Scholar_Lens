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
