from django.contrib import admin
from .models import AIAnalysis, ResearchGap, ChatMessage

@admin.register(AIAnalysis)
class AIAnalysisAdmin(admin.ModelAdmin):
    list_display = ('paper', 'analysis_type', 'model_name', 'tokens_used', 'created_at')
    list_filter = ('analysis_type', 'model_name', 'created_at')
    search_fields = ('paper__title', 'prompt_used')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ResearchGap)
class ResearchGapAdmin(admin.ModelAdmin):
    list_display = ('title', 'paper', 'area', 'severity', 'created_at')
    list_filter = ('severity', 'area', 'created_at')
    search_fields = ('title', 'description', 'paper__title')
    readonly_fields = ('created_at',)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('paper', 'user', 'question_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('question', 'answer', 'paper__title', 'user__username')
    readonly_fields = ('created_at',)

    def question_preview(self, obj):
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Question'

