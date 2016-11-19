from django.db import models

from ale.models import AleExperiment

from seq.models import Mutation


class FixatedMutation(models.Model):

    ale_experiment = models.ForeignKey(AleExperiment,
                                       on_delete=models.CASCADE)

    mutation = models.ForeignKey(Mutation,
                                 null=True)

    fixed_observed_mutation_series = models.CharField(max_length=500, default='', blank=True)