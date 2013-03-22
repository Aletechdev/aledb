from django.db import models

# Create your models here.
class ResequencingExperiment(models.Model):
    isolate = models.ForeignKey("ale.Isolate")
    #person = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    person = models.CharField(max_length=200, blank=True)
    reads = models.IntegerField(blank=True, null=True)
    average_read_length = models.FloatField(blank=True, null=True)
    mutations = models.ManyToManyField("Mutation", through="ObservedMutation")
    location = models.CharField(max_length=200, blank=True, null=True)
    mean_coverage = models.FloatField(blank=True, null=True)
    percentage_mapped = models.FloatField(blank=True, null=True)
    #@property
    #def mean_coverage(self):
    #    return self.average_read_length * self.reads / 4639675.
    
    @property
    def ale_id(self):
        return self.isolate.flask.ale_id.ale_id
    @property
    def flask_number(self):
        return self.isolate.flask.flask_number
    
    def get_isolate_name(self):
        return u"A%d_F%d_I%d" % (self.ale_id, self.flask_number, self.isolate.isolate_number)
    # TODO - add more information

class Mutation(models.Model):
    #type = models.CharField(max_length=5)
    position = models.IntegerField()
    feature_length = models.IntegerField(blank=True, null=True)
    sequence_change = models.CharField(max_length=100)
    protein_change = models.CharField(max_length=300, blank=True, null=True)
    gene = models.CharField(max_length=300, blank=True, null=True)
    reference_error = models.NullBooleanField(default=False)
    class Meta:
        unique_together = (("position", "sequence_change"),)

class ObservedMutation(models.Model):
    sequencing_experiment = models.ForeignKey(ResequencingExperiment)
    mutation = models.ForeignKey(Mutation)
    percentage = models.FloatField(blank=True, null=True)
    evidence = models.CharField(max_length=400, blank=True, null=True)
