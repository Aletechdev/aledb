from django.db import models

from ale.models import AleExperiment

from filter.common import DEFAULT_MUTATION_FREQ_MIN
from filter.common import DEFAULT_MUTATION_FREQ_MAX


class AleExperimentFilter(models.Model):

    ale_experiment = models.ForeignKey(AleExperiment, on_delete=models.CASCADE)
    min_cutoff = models.PositiveSmallIntegerField(default=DEFAULT_MUTATION_FREQ_MIN)  # TODO: this should like rather be a decimal to it's conterpart of seq.models.ObservedMutation.frequency
    max_cutoff = models.PositiveSmallIntegerField(default=DEFAULT_MUTATION_FREQ_MAX)  # TODO: this should like rather be a decimal to it's conterpart of seq.models.ObservedMutation.frequency
    ignored_genes = models.CharField(max_length=500, default='', blank=True)
    ignored_mutations = models.CharField(max_length=500, default='', blank=True)
    starting_strain_mutations = models.CharField(max_length=500, default='', blank=True)


class GlobalFilter(models.Model):

    ignored_genes = models.CharField(max_length=500, default='', blank=True)
    ignored_mutations = models.CharField(max_length=500, default='', blank=True)
