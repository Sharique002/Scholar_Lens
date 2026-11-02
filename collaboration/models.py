from django.db import models
from django.contrib.auth.models import User
from projects.models import ResearchProject

class CollaborationRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
        ('CANCELLED', 'Cancelled'),
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_collaboration_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_collaboration_requests')
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    project = models.ForeignKey(ResearchProject, on_delete=models.CASCADE, null=True, blank=True, related_name='collaboration_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['sender']),
            models.Index(fields=['receiver']),
        ]

    def __str__(self):
        return f"Request from {self.sender.username} to {self.receiver.username} ({self.status})"


class CollaborationSuggestion(models.Model):
    researcher = models.ForeignKey(
        'researchers.ResearcherProfile',
        on_delete=models.CASCADE,
        related_name='received_suggestions'
    )
    suggested = models.ForeignKey(
        'researchers.ResearcherProfile',
        on_delete=models.CASCADE,
        related_name='target_suggestions'
    )
    score = models.FloatField()
    adjacency_score = models.FloatField(default=0.0)
    gap_score = models.FloatField(default=0.0)
    explanation = models.JSONField(default=dict)
    is_dismissed = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-score']
        unique_together = ('researcher', 'suggested')
        indexes = [
            models.Index(fields=['researcher', 'is_dismissed']),
            models.Index(fields=['score']),
        ]

    def __str__(self):
        return f"Suggestion: {self.researcher.user.username} -> {self.suggested.user.username} ({self.score})"
