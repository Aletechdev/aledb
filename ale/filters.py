from django_filters import FilterSet
from .models import AleExperiment, Project


class AleExperimentFilter(FilterSet):
    class Meta:
        model = AleExperiment
        fields = {"name": ["contains"], "person": ["contains"]}


class ProjectFilter(FilterSet):
    class Meta:
        model = Project
        fields = {"name": ["contains"], "description": ["contains"]}


