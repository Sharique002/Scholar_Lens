from django.contrib import admin
from .models import ResearchOpening, OpportunityApplication


@admin.register(ResearchOpening)
class ResearchOpeningAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'department', 'spots_available', 'deadline', 'status', 'created_by')
    list_filter = ('status', 'department')
    search_fields = ('title', 'description')


@admin.register(OpportunityApplication)
class OpportunityApplicationAdmin(admin.ModelAdmin):
    list_display = ('opening', 'applicant', 'status', 'created_at', 'reviewed_by')
    list_filter = ('status', 'created_at')
    search_fields = ('applicant__username', 'opening__title', 'statement')
