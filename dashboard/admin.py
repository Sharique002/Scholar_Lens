from django.contrib import admin
from .models import ResearchActivity, AuditEntry


@admin.register(ResearchActivity)
class ResearchActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__username', 'description')


@admin.register(AuditEntry)
class AuditEntryAdmin(admin.ModelAdmin):
    list_display = ('action', 'actor', 'target_type', 'target_id', 'created_at')
    list_filter = ('action', 'target_type', 'created_at')
    search_fields = ('action', 'actor__username', 'target_type')
    readonly_fields = ('actor', 'action', 'target_type', 'target_id', 'data', 'created_at')
