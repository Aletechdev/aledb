from django.db import models

from ale.models import AleExperiment

from seq.models import Mutation


class ConvergeMutation(models.Model):

    ale_experiment = models.ForeignKey(AleExperiment,
                                       on_delete=models.CASCADE)

    mutation = models.ForeignKey(Mutation,
                                 null=True)
