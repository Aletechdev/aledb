from django.contrib import admin
from django import forms
from filter.models import AleExperimentFilter
from guardian.admin import GuardedModelAdmin


@admin.register(AleExperimentFilter)
class FilterAdmin(GuardedModelAdmin):
    list_display = ('id', 'ale_experiment', 'min_cutoff', 'max_cutoff')
    search_fields = ('id', 'ale_experiment')
