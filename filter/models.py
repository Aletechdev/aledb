from django.db import models

from ale.models import AleExperiment

from filter.common import DEFAULT_MUTATION_FREQ_MIN
from filter.common import DEFAULT_MUTATION_FREQ_MAX


class AleExperimentFilter(models.Model):

    ale_experiment = models.ForeignKey(AleExperiment, on_delete=models.CASCADE)
    min_cutoff = models.PositiveSmallIntegerField(default=DEFAULT_MUTATION_FREQ_MIN)
    max_cutoff = models.PositiveSmallIntegerField(default=DEFAULT_MUTATION_FREQ_MAX)
    ignored_genes = models.CharField(max_length=500, default='', blank=True)
    ignored_mutations = models.TextField(default='', blank=True)


class GlobalFilter(models.Model):

    ignored_genes = models.CharField(max_length=500, default='', blank=True)
    ignored_mutations = models.TextField(default='', blank=True)
