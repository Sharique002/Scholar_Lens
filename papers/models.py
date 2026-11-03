from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.indexes import GinIndex

from .text import normalise_title


class ActivePaperManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(merged_into__isnull=True)


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

    doi = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Digital Object Identifier (DOI).")
    )
    normalised_title = models.CharField(
        max_length=512,
        blank=True,
        default='',
        db_index=True,
        help_text=_("Lowercased, unaccented, punctuation-free title for deduplication.")
    )
    venue = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text=_("Journal, conference, or workshop venue name.")
    )
    pub_type = models.CharField(
        max_length=50,
        blank=True,
        default='JOURNAL',
        choices=[
            ('JOURNAL', _('Journal')),
            ('CONFERENCE', _('Conference')),
            ('BOOK', _('Book')),
            ('PREPRINT', _('Preprint')),
            ('OTHER', _('Other')),
        ],
        help_text=_("Publication type.")
    )
    year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Publication year.")
    )
    merged_into = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='merged_copies',
        help_text=_("Canonical paper this record was merged into (soft merge).")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActivePaperManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ['-created_at']
        base_manager_name = 'all_objects'
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['research_area']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_external', 'created_at']),
            models.Index(fields=['source', 'external_id']),
            models.Index(fields=['publication_date']),
            models.Index(fields=['doi']),
            models.Index(fields=['year']),
            GinIndex(fields=['normalised_title'], opclasses=['gin_trgm_ops'], name='paper_title_trgm'),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.normalised_title and self.title:
            self.normalised_title = normalise_title(self.title)
        if not self.year and self.publication_date:
            self.year = self.publication_date.year
        super().save(*args, **kwargs)

    def resolve(self):
        """Follow merged_into chain until canonical record is reached."""
        curr = self
        visited = {curr.pk}
        while curr.merged_into_id:
            if curr.merged_into_id in visited:
                break
            curr = curr.merged_into
            visited.add(curr.pk)
        return curr

    @property
    def merged_copies_all(self):
        return ResearchPaper.all_objects.filter(merged_into=self)


class PaperAuthor(models.Model):
    class MatchStatus(models.TextChoices):
        UNMATCHED = 'UNMATCHED', _('Unmatched')
        PENDING_REVIEW = 'PENDING_REVIEW', _('Pending Review')
        CONFIRMED = 'CONFIRMED', _('Confirmed')
        REJECTED = 'REJECTED', _('Rejected')

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

    orcid = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    researcher = models.ForeignKey(
        'researchers.ResearcherProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='authored_papers'
    )
    match_status = models.CharField(
        max_length=20,
        choices=MatchStatus.choices,
        default=MatchStatus.UNMATCHED,
        db_index=True
    )
    match_score = models.FloatField(null=True, blank=True)
    matched_at = models.DateTimeField(null=True, blank=True)
    matched_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['match_status']),
            models.Index(fields=['orcid']),
        ]

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


class DuplicateCandidate(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        MERGED = 'MERGED', _('Merged')
        DISMISSED = 'DISMISSED', _('Dismissed')

    incoming_paper = models.ForeignKey(
        ResearchPaper,
        on_delete=models.CASCADE,
        related_name='duplicate_candidates_as_incoming'
    )
    existing_paper = models.ForeignKey(
        ResearchPaper,
        on_delete=models.CASCADE,
        related_name='duplicate_candidates_as_existing'
    )
    similarity_score = models.FloatField(help_text=_("Fuzzy matching score (0-100)."))
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"DuplicateCandidate: #{self.incoming_paper_id} -> #{self.existing_paper_id} ({self.similarity_score:.1f}%)"


class ImportRun(models.Model):
    class Source(models.TextChoices):
        ORCID = 'ORCID', _('ORCID')
        CROSSREF = 'CROSSREF', _('Crossref')

    class Status(models.TextChoices):
        STARTED = 'STARTED', _('Started')
        SUCCESS = 'SUCCESS', _('Success')
        FAILED = 'FAILED', _('Failed')

    source = models.CharField(max_length=50, choices=Source.choices)
    query = models.CharField(max_length=255)
    total_fetched = models.PositiveIntegerField(default=0)
    imported_count = models.PositiveIntegerField(default=0)
    duplicate_count = models.PositiveIntegerField(default=0)
    skipped_malformed = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.STARTED)
    error_message = models.TextField(blank=True, default='')
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='import_runs'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"ImportRun {self.source} '{self.query}' ({self.status}) - {self.imported_count} imported"
