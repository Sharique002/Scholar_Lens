from django.contrib import admin
from .models import CollaborationRequest

@admin.register(CollaborationRequest)
class CollaborationRequestAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'status', 'project', 'created_at')
    search_fields = ('sender__username', 'receiver__username', 'message')
    list_filter = ('status',)
