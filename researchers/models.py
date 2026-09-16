from django.db import models
from django.contrib.auth.models import User

class ResearchInterest(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Skill(models.Model):
    SKILL_CATEGORIES = (
        ('PROGRAMMING', 'Programming Language'),
        ('FRAMEWORK', 'Framework/Library'),
        ('TOOL', 'Software/Tool'),
        ('METHOD', 'Methodology'),
        ('DOMAIN', 'Domain Knowledge'),
        ('OTHER', 'Other'),
    )
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=SKILL_CATEGORIES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ResearcherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='researcher_profile')
    headline = models.CharField(max_length=200, blank=True)
    expertise_summary = models.TextField(blank=True)
    google_scholar_url = models.URLField(blank=True)
    orcid_id = models.CharField(max_length=50, blank=True)
    years_experience = models.PositiveIntegerField(default=0)
    interests = models.ManyToManyField(ResearchInterest, blank=True, related_name='researchers')
    skills = models.ManyToManyField(Skill, blank=True, related_name='researchers')
    is_available_for_collaboration = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Researcher Profile: {self.user.username}"

