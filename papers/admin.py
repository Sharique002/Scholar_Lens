from django.contrib import admin
from .models import ResearchPaper, PaperAuthor, PaperChunk, PaperEmbedding, DuplicateCandidate, ImportRun


class PaperAuthorInline(admin.TabularInline):
    model = PaperAuthor
    extra = 1


@admin.register(ResearchPaper)
class ResearchPaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploader', 'venue', 'year', 'pub_type', 'doi', 'status', 'merged_into', 'created_at')
    list_filter = ('status', 'research_area', 'pub_type', 'year')
    search_fields = ('title', 'normalised_title', 'doi', 'abstract', 'keywords')
    inlines = [PaperAuthorInline]


@admin.register(DuplicateCandidate)
class DuplicateCandidateAdmin(admin.ModelAdmin):
    list_display = ('id', 'incoming_paper', 'existing_paper', 'similarity_score', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('incoming_paper__title', 'existing_paper__title')


@admin.register(PaperChunk)
class PaperChunkAdmin(admin.ModelAdmin):
    list_display = ('paper', 'chunk_index', 'token_count', 'created_at')
    list_filter = ('paper',)
    search_fields = ('content',)


admin.site.register(PaperEmbedding)


@admin.register(ImportRun)
class ImportRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'source', 'query', 'imported_count', 'duplicate_count', 'skipped_malformed', 'status', 'created_at')
    list_filter = ('source', 'status')
    search_fields = ('query',)
