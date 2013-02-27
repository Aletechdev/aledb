from django.db import models

# Create your models here.
class ResequencingExperiment(models.Model):
    isolate = models.ForeignKey("ale.Isolate")
    #person = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    person = models.CharField(max_length=200, blank=True)
    reads = models.IntegerField(blank=True, null=True)
    average_read_length = models.FloatField(blank=True, null=True)
    mutations = models.ManyToManyField("Mutation", through="ObservedMutation")
    # TODO - add more information

class Mutation(models.Model):
    #type = models.CharField(max_length=5)
    position = models.IntegerField()
    feature_length = models.IntegerField(blank=True, null=True)
    sequence_change = models.CharField(max_length=100)
    class Meta:
        unique_together = (("position", "sequence_change"),)

class ObservedMutation(models.Model):
    sequencing_experiment = models.ForeignKey(ResequencingExperiment)
    mutation = models.ForeignKey(Mutation)
    percentage = models.FloatField(blank=True, null=True)
