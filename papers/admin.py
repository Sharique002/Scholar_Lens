from django.contrib import admin
from .models import ResearchPaper, PaperAuthor, PaperChunk, PaperEmbedding


class PaperAuthorInline(admin.TabularInline):
    model = PaperAuthor
    extra = 1


@admin.register(ResearchPaper)
class ResearchPaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploader', 'venue', 'year', 'pub_type', 'doi', 'status', 'merged_into', 'created_at')
    list_filter = ('status', 'research_area', 'pub_type', 'year')
    search_fields = ('title', 'normalised_title', 'doi', 'abstract', 'keywords')
    inlines = [PaperAuthorInline]


@admin.register(PaperChunk)
class PaperChunkAdmin(admin.ModelAdmin):
    list_display = ('paper', 'chunk_index', 'token_count', 'created_at')
    list_filter = ('paper',)
    search_fields = ('content',)


admin.site.register(PaperEmbedding)
