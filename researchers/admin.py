from django.contrib import admin
from .models import Department, ResearchInterest, Skill, ResearcherProfile


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')


@admin.register(ResearchInterest)
class ResearchInterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'parent', 'created_at')
    search_fields = ('name', 'category')
    list_filter = ('category', 'parent')


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'created_at')
    search_fields = ('name',)
    list_filter = ('category',)


@admin.register(ResearcherProfile)
class ResearcherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'verification_status', 'headline', 'is_available_for_collaboration', 'updated_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'headline', 'orcid_id')
    list_filter = ('verification_status', 'department', 'is_available_for_collaboration')
    filter_horizontal = ('interests', 'skills')
