from django.db import models

from ale.models import AleExperiment

from filter.common import DEFAULT_MUTATION_FREQ_MIN
from filter.common import DEFAULT_MUTATION_FREQ_MAX


def get_default_experiment_filter_params(ale_experiment):
    default_experiment_filter_params = {
            'ale_experiment': ale_experiment,
            'min_cutoff': DEFAULT_MUTATION_FREQ_MIN,
            'max_cutoff': DEFAULT_MUTATION_FREQ_MAX,
            'min_gatk_cutoff': DEFAULT_MUTATION_FREQ_MIN,
            'max_gatk_cutoff': DEFAULT_MUTATION_FREQ_MAX,
            'ignored_genes': "",
            'ignored_mutations': ""}
    return default_experiment_filter_params


class AleExperimentFilter(models.Model):

    ale_experiment = models.ForeignKey(AleExperiment, on_delete=models.CASCADE)
    min_cutoff = models.PositiveSmallIntegerField(default=DEFAULT_MUTATION_FREQ_MIN)  # TODO: this should like rather be a decimal to it's conterpart of seq.models.ObservedMutation.frequency
    max_cutoff = models.PositiveSmallIntegerField(default=DEFAULT_MUTATION_FREQ_MAX)  # TODO: this should like rather be a decimal to it's conterpart of seq.models.ObservedMutation.frequency
    min_gatk_cutoff = models.PositiveSmallIntegerField(
        default=DEFAULT_MUTATION_FREQ_MIN)  # TODO: this should like rather be a decimal to it's conterpart of seq.models.ObservedMutation.frequency
    max_gatk_cutoff = models.PositiveSmallIntegerField(
        default=DEFAULT_MUTATION_FREQ_MAX)  # TODO: this should like rather be a decimal to it's conterpart of seq.models.ObservedMutation.frequency

    ignored_genes = models.TextField(default='', blank=True)
    ignored_mutations = models.CharField(max_length=5000, default='', blank=True)
    starting_strain_mutations = models.CharField(max_length=5000, default='', blank=True)


class GlobalFilter(models.Model):

    ignored_genes = models.CharField(max_length=5000, default='', blank=True)
    ignored_mutations = models.CharField(max_length=5000, default='', blank=True)
