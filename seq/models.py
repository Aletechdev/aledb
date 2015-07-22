from django.db import models


class ResequencingExperiment(models.Model):

    isolate = models.ForeignKey("ale.Isolate")

    person = models.CharField(max_length=200,
                              blank=True)

    reads = models.IntegerField(blank=True,
                                null=True)

    average_read_length = models.FloatField(blank=True,
                                            null=True)

    mutations = models.ManyToManyField("Mutation",
                                       through="ObservedMutation")

    location = models.CharField(max_length=200,
                                blank=True,
                                null=True)

    mean_coverage = models.FloatField(blank=True,
                                      null=True)

    percentage_mapped = models.FloatField(blank=True,
                                          null=True)

    @property
    def ale_id(self):

        return self.isolate.flask.ale_id.ale_id

    @property
    def flask_number(self):

        return self.isolate.flask.flask_number

    def get_isolate_name(self):

        if self.isolate.description is not None:

            if len(self.isolate.description) > 0:
                return self.isolate.description

        return u"A%d_F%d_I%d" % (self.ale_id, self.flask_number, self.isolate.isolate_number)

        # TODO - add more information


class UnassignedMissingCoverageEvidence(models.Model):

    seq_id = models.CharField(max_length=100)

    start = models.IntegerField()

    end = models.IntegerField()

    sequencing_experiment = models.ForeignKey(ResequencingExperiment)



class Mutation(models.Model):

    mutation_type = models.CharField(max_length=3,
                                     null=True,
                                     help_text="""Use breseq mutation codes, see the genome diff site
                                     on the barrick lab wiki (http://tinyurl.com/l3fvnap) for more
                                     information""")

    position = models.IntegerField()

    # frequency = models.CharField(max_length=100,blank=True,null=True)

    feature_length = models.IntegerField(blank=True,
                                         null=True)

    sequence_change = models.CharField(max_length=100)

    protein_change = models.CharField(max_length=300,
                                      blank=True,
                                      null=True)

    gene = models.CharField(max_length=300,
                            blank=True,
                            null=True)

    reference_error = models.NullBooleanField(default=False)

    def __unicode__(self):
        return u"%d %s" % (self.position,
                           self.sequence_change)

    class Meta:
        unique_together = (("position",
                            "sequence_change"),)


class ObservedMutation(models.Model):

    present = models.NullBooleanField()

    breseq_present = models.NullBooleanField()

    wt_reads = models.IntegerField(null=True)

    mutated_reads = models.IntegerField(null=True)

    other_reads = models.IntegerField(null=True)

    reference_genome_likelihood = models.FloatField(null=True)

    sequencing_experiment = models.ForeignKey(ResequencingExperiment)

    mutation = models.ForeignKey(Mutation)

    evidence = models.CharField(max_length=400,
                                blank=True,
                                null=True)

    frequency = models.CharField(max_length=100,
                                 blank=True,
                                 null=True)
