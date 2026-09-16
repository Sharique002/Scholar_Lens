import uuid
from django.db import models

class EvaluationReport(models.Model):
    evaluation_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    paper = models.ForeignKey('papers.ResearchPaper', on_delete=models.CASCADE, related_name='evaluation_reports')
    overall_score = models.FloatField(default=0)
    summary = models.TextField(blank=True)
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    concerns = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    similar_papers = models.JSONField(default=list)
    disclaimer = models.TextField(default='This AI-generated assessment is an analytical aid and does not certify research originality, novelty, plagiarism status, patentability, or publication acceptance.')
    model_name = models.CharField(max_length=100, default='gpt-4o-mini')
    provider = models.CharField(max_length=50, default='openai')
    model_version = models.CharField(max_length=100, default='gpt-4o-mini')
    prompt_version = models.CharField(max_length=50, default='v2.0-canonical-7dim')
    scoring_framework_version = models.CharField(max_length=50, default='v2-7dim-100pt')
    paper_version = models.IntegerField(default=1)
    retrieved_sources = models.JSONField(default=list, blank=True)
    confidence = models.CharField(max_length=20, default='Medium', choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')])
    limitations = models.TextField(blank=True, default='Similarity analysis and automated evaluation cannot establish definitive originality or peer-reviewed certification. Further domain literature review is recommended.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']

    # 7 Canonical Dimension Property Getters
    @property
    def novelty_score(self):
        s = self.scores.filter(dimension='NOVELTY').first()
        return s.score if s else 0.0

    @property
    def research_gap_score(self):
        s = self.scores.filter(dimension='RESEARCH_GAP').first()
        return s.score if s else 0.0

    @property
    def methodology_score(self):
        s = self.scores.filter(dimension='METHODOLOGY').first()
        return s.score if s else 0.0

    @property
    def contribution_score(self):
        s = self.scores.filter(dimension='CONTRIBUTION').first()
        return s.score if s else 0.0

    @property
    def evidence_quality_score(self):
        s = self.scores.filter(dimension__in=['EVIDENCE_QUALITY', 'EVIDENCE']).first()
        return s.score if s else 0.0

    @property
    def technical_strength_score(self):
        s = self.scores.filter(dimension='TECHNICAL_STRENGTH').first()
        return s.score if s else 0.0

    @property
    def clarity_score(self):
        s = self.scores.filter(dimension='CLARITY').first()
        return s.score if s else 0.0

    # Backward-compatible property aliases
    @property
    def rigor_score(self):
        return self.methodology_score

    @property
    def impact_score(self):
        return self.contribution_score

    @property
    def reproducibility_score(self):
        return self.evidence_quality_score

    @property
    def ethical_score(self):
        return self.research_gap_score

    @property
    def recommendation(self):
        if self.recommendations and len(self.recommendations) > 0:
            return self.recommendations[0] if isinstance(self.recommendations, list) else str(self.recommendations)
        return "ACCEPT" if self.overall_score >= 70 else "REVISE"

    @property
    def summary_verdict(self):
        return self.summary

    def __str__(self):
        return f"Evaluation v{self.paper_version} for {self.paper.title} ({self.overall_score:.1f})"


class ResearchScore(models.Model):
    SCORE_DIMENSION_CHOICES = [
        ('NOVELTY', 'Potential Novelty'),
        ('RESEARCH_GAP', 'Research Gap'),
        ('METHODOLOGY', 'Methodology'),
        ('CONTRIBUTION', 'Contribution'),
        ('EVIDENCE_QUALITY', 'Evidence Quality'),
        ('TECHNICAL_STRENGTH', 'Technical Strength'),
        ('CLARITY', 'Clarity'),
        # Backward compatibility aliases
        ('EVIDENCE', 'Evidence Quality'),
    ]

    report = models.ForeignKey(EvaluationReport, on_delete=models.CASCADE, related_name='scores')
    dimension = models.CharField(max_length=50, choices=SCORE_DIMENSION_CHOICES)
    score = models.FloatField(default=0)  # 0-100
    weight = models.FloatField(default=1.0)
    explanation = models.TextField()
    supporting_evidence = models.JSONField(default=list, blank=True)
    confidence = models.CharField(max_length=20, default='Medium', choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')])
    limitations = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['report', 'dimension']

    def __str__(self):
        return f"{self.get_dimension_display()}: {self.score}/100"
