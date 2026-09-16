from django.contrib import admin
from .models import EvaluationReport, ResearchScore

class ResearchScoreInline(admin.TabularInline):
    model = ResearchScore
    extra = 0

@admin.register(EvaluationReport)
class EvaluationReportAdmin(admin.ModelAdmin):
    list_display = ('paper', 'overall_score', 'created_at')
    inlines = [ResearchScoreInline]
