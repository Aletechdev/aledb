from django.contrib import admin
from django import forms
from ale.models import Project, AleExperiment, Media
from guardian.admin import GuardedModelAdmin


class ExperimentInline(admin.TabularInline):
    model = AleExperiment
    extra = 0
    fields = ('name', 'person')


@admin.register(AleExperiment)
class AleExperimentAdmin(admin.ModelAdmin):
    # fetch project
    list_select_related = ('project',)
    list_display = ('ale_id', 'name', 'project', 'person', 'date')
    search_fields = ('name', 'person', 'project')


@admin.register(Project)
class ProjectAdmin(GuardedModelAdmin):
    list_display = ('id', 'name', 'user', 'date', 'status', 'is_public')
    search_fields = ('name', 'user')
    # inlines = [ExperimentInline]


@admin.register(Media)
class MediaAdmin(GuardedModelAdmin):
    list_display = ('id', 'description')
    search_fields = ('name', 'user')
    # inlines = [ExperimentInline]