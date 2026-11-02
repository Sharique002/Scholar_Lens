from django.contrib import admin
from .models import FundingCall, FundingAlert


@admin.register(FundingCall)
class FundingCallAdmin(admin.ModelAdmin):
    list_display = ('title', 'sponsor', 'deadline', 'is_published')
    list_filter = ('research_area', 'is_published')
    search_fields = ('title', 'sponsor', 'description')
    date_hierarchy = 'deadline'


@admin.register(FundingAlert)
class FundingAlertAdmin(admin.ModelAdmin):
    list_display = ('call', 'user', 'days_before', 'sent_at')
    list_filter = ('days_before', 'sent_at')
    search_fields = ('call__title', 'user__username')
