from django.db import models
from django.contrib.auth.models import User

class AIAnalysis(models.Model):
    ANALYSIS_TYPE_CHOICES = [
        ('SUMMARY', 'Summary'),
        ('RESEARCH_GAPS', 'Research Gaps'),
        ('QUESTION_ANSWER', 'Question Answer'),
        ('EVALUATION', 'Evaluation'),
        ('SIMILARITY', 'Similarity'),
    ]

    paper = models.ForeignKey('papers.ResearchPaper', on_delete=models.CASCADE, related_name='ai_analyses')
    analysis_type = models.CharField(max_length=50, choices=ANALYSIS_TYPE_CHOICES)
    result = models.JSONField()
    prompt_used = models.TextField(blank=True)
    model_name = models.CharField(max_length=100, default='gpt-4o-mini')
    tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['paper', 'analysis_type']),
        ]

    @property
    def executive_summary(self):
        if isinstance(self.result, dict):
            return self.result.get('executive_summary', '')
        return str(self.result) if self.result else ''

    @property
    def methodology_summary(self):
        return self.result.get('methodology_summary', '') if isinstance(self.result, dict) else ''

    @property
    def key_findings(self):
        return self.result.get('key_findings', '') if isinstance(self.result, dict) else ''

    @property
    def limitations(self):
        return self.result.get('limitations', '') if isinstance(self.result, dict) else ''

    @property
    def future_work(self):
        return self.result.get('future_work', '') if isinstance(self.result, dict) else ''


class ResearchGap(models.Model):
    SEVERITY_CHOICES = [
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]

    paper = models.ForeignKey('papers.ResearchPaper', on_delete=models.CASCADE, related_name='research_gaps')
    title = models.CharField(max_length=255)
    description = models.TextField()
    area = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    suggestions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def gap_type(self):
        return self.severity

    @property
    def suggested_directions(self):
        return self.suggestions


class ChatMessage(models.Model):
    paper = models.ForeignKey('papers.ResearchPaper', on_delete=models.CASCADE, related_name='chat_messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
