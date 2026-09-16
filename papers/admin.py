from django.contrib import admin
from .models import ResearchPaper, PaperAuthor, PaperChunk, PaperEmbedding


class PaperAuthorInline(admin.TabularInline):
    model = PaperAuthor
    extra = 1


@admin.register(ResearchPaper)
class ResearchPaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploader', 'research_area', 'status', 'created_at')
    list_filter = ('status', 'research_area')
    search_fields = ('title', 'abstract', 'keywords')
    inlines = [PaperAuthorInline]


@admin.register(PaperChunk)
class PaperChunkAdmin(admin.ModelAdmin):
    list_display = ('paper', 'chunk_index', 'token_count', 'created_at')
    list_filter = ('paper',)
    search_fields = ('content',)
    
admin.site.register(PaperEmbedding)
