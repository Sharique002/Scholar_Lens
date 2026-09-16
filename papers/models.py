from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ResearchPaper(models.Model):
    class PaperStatus(models.TextChoices):
        UPLOADED = 'UPLOADED', _('Uploaded')
        TEXT_EXTRACTED = 'TEXT_EXTRACTED', _('Text Extracted')
        INDEXED = 'INDEXED', _('Indexed')
        AI_ANALYZED = 'AI_ANALYZED', _('AI Analyzed')
        EVALUATED = 'EVALUATED', _('Evaluated')
        FAILED = 'FAILED', _('Failed')

    class ResearchArea(models.TextChoices):
        AI_ML = 'AI_ML', _('Artificial Intelligence & Machine Learning')
        NLP = 'NLP', _('Natural Language Processing')
        COMPUTER_VISION = 'COMPUTER_VISION', _('Computer Vision')
        DATA_SCIENCE = 'DATA_SCIENCE', _('Data Science')
        CYBERSECURITY = 'CYBERSECURITY', _('Cybersecurity')
        SOFTWARE_ENGINEERING = 'SOFTWARE_ENGINEERING', _('Software Engineering')
        NETWORKING = 'NETWORKING', _('Networking')
        DATABASE = 'DATABASE', _('Database Systems')
        HCI = 'HCI', _('Human-Computer Interaction')
        ROBOTICS = 'ROBOTICS', _('Robotics')
        BIOINFORMATICS = 'BIOINFORMATICS', _('Bioinformatics')
        QUANTUM_COMPUTING = 'QUANTUM_COMPUTING', _('Quantum Computing')
        OTHER = 'OTHER', _('Other')

    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_papers',
        help_text=_("The user who uploaded this paper, or null for externally discovered papers.")
    )
    title = models.CharField(max_length=512, help_text=_("Title of the research paper."))
    abstract = models.TextField(help_text=_("Abstract of the paper."))
    research_area = models.CharField(
        max_length=50,
        choices=ResearchArea.choices,
        default=ResearchArea.OTHER,
        help_text=_("Primary research area.")
    )
    keywords = models.CharField(
        max_length=255,
        help_text=_("Comma-separated list of keywords.")
    )
    status = models.CharField(
        max_length=50,
        choices=PaperStatus.choices,
        default=PaperStatus.UPLOADED,
        help_text=_("Current processing status of the paper.")
    )
    pdf_file = models.FileField(
        upload_to='papers/',
        blank=True,
        null=True,
        help_text=_("The uploaded PDF file of the paper.")
    )
    extracted_text = models.TextField(
        blank=True,
        help_text=_("Full text extracted from the PDF.")
    )
    page_count = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Number of pages in the PDF.")
    )
    word_count = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Approximate word count of the extracted text.")
    )
    source = models.CharField(
        max_length=50,
        default='USER_UPLOAD',
        choices=[
            ('USER_UPLOAD', _('User Upload')),
            ('GOOGLE_SCHOLAR', _('Google Scholar')),
            ('EXTERNAL', _('External Source')),
        ],
        db_index=True,
        help_text=_("Source of the research paper.")
    )
    external_id = models.CharField(
        max_length=255,
        blank=True,
        default='',
        db_index=True,
        help_text=_("External unique identifier or cluster ID.")
    )
    external_url = models.URLField(
        max_length=1024,
        blank=True,
        default='',
        help_text=_("Original external URL / paper link.")
    )
    publication_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Actual date when paper was published.")
    )
    citation_count = models.IntegerField(
        default=0,
        null=True,
        blank=True,
        help_text=_("Citation count reported by external source.")
    )
    is_external = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_("Whether this paper was discovered externally rather than uploaded.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['research_area']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_external', 'created_at']),
            models.Index(fields=['source', 'external_id']),
            models.Index(fields=['publication_date']),
        ]

    def __str__(self):
        return self.title


class PaperAuthor(models.Model):
    paper = models.ForeignKey(
        ResearchPaper,
        on_delete=models.CASCADE,
        related_name='authors'
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    affiliation = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=1)
    is_corresponding = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class PaperChunk(models.Model):
    paper = models.ForeignKey(
        ResearchPaper,
        on_delete=models.CASCADE,
        related_name='chunks'
    )
    chunk_index = models.IntegerField()
    page_number = models.IntegerField(default=1, null=True, blank=True, help_text=_("PDF page number where this chunk originates."))
    section = models.CharField(max_length=200, blank=True, default='Body', help_text=_("Detected academic section header."))
    start_offset = models.IntegerField(default=0, help_text=_("Character start offset within extracted text."))
    end_offset = models.IntegerField(default=0, help_text=_("Character end offset within extracted text."))
    content = models.TextField()
    token_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['chunk_index']
        unique_together = ('paper', 'chunk_index')

    def __str__(self):
        return f"Chunk {self.chunk_index} (p.{self.page_number}, {self.section}) of {self.paper.title}"


class PaperEmbedding(models.Model):
    chunk = models.OneToOneField(
        PaperChunk,
        on_delete=models.CASCADE,
        related_name='embedding'
    )
    embedding = models.JSONField(help_text=_("Vector embedding representation of the chunk."))
    model_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Embedding for chunk {self.chunk.id}"
