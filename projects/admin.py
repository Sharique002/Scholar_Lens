from django.contrib import admin
from .models import ResearchProject, ProjectMember

@admin.register(ResearchProject)
class ResearchProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'leader', 'status', 'research_area', 'is_public', 'created_at')
    search_fields = ('title', 'description', 'leader__username')
    list_filter = ('status', 'research_area', 'is_public')

@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'role', 'joined_at')
    search_fields = ('project__title', 'user__username')
    list_filter = ('role',)
