from django.db import models
from django.conf import settings

class ResearchActivity(models.Model):
    ACTIVITY_TYPES = (
        ('PAPER_UPLOAD', 'Paper Upload'),
        ('PAPER_EDIT', 'Paper Edit'),
        ('AI_ANALYSIS', 'AI Analysis'),
        ('EVALUATION', 'Evaluation'),
        ('COLLABORATION', 'Collaboration'),
        ('PROJECT', 'Project'),
        ('SEARCH', 'Search'),
        ('LOGIN', 'Login'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField()
    related_paper = models.ForeignKey('papers.ResearchPaper', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
