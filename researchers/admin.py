from django.contrib import admin
from .models import ResearchInterest, Skill, ResearcherProfile

@admin.register(ResearchInterest)
class ResearchInterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'created_at')
    search_fields = ('name', 'category')
    list_filter = ('category',)

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'created_at')
    search_fields = ('name',)
    list_filter = ('category',)

@admin.register(ResearcherProfile)
class ResearcherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'headline', 'is_available_for_collaboration', 'updated_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'headline')
    list_filter = ('is_available_for_collaboration',)
    filter_horizontal = ('interests', 'skills')
