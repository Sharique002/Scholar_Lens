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
