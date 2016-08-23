from django.db import models

blank_field = {"blank": True, "null": True}


# TODO: Refacor: figure out how to get a ResequencingExperiment to return its list of observed mutations and remove functionality from seq.views.common
class ResequencingExperiment(models.Model):

    tech_rep = models.ForeignKey("ale.TechnicalReplicate", null=True)

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
    def ale_experiment(self):
        return self.tech_rep.isolate.flask.ale_id.ale_experiment

    @property
    def ale_id(self):
        return self.tech_rep.isolate.flask.ale_id.ale_id

    @property
    def flask_number(self):
        return self.tech_rep.isolate.flask.flask_number

    @property
    def ale_flask_isolate_str(self):

        if self.tech_rep.isolate.description is not None:

            if len(self.tech_rep.isolate.description) > 0:

                return self.tech_rep.isolate.description

        return u"A%d F%d I%d R%d" % (self.ale_id,
                                     self.flask_number,
                                     self.tech_rep.isolate.isolate_number,
                                     self.tech_rep.tech_rep_number)

    @property
    def aleexp_ale_flask_isolate_str(self):
        return self.ale_experiment.name + " " + self.ale_flask_isolate_str


class UnassignedMissingCoverageEvidence(models.Model):

    seq_id = models.CharField(max_length=100)

    start = models.IntegerField()

    end = models.IntegerField()

    sequencing_experiment = models.ForeignKey(ResequencingExperiment,
                                              on_delete=models.CASCADE)


class Mutation(models.Model):

    mutation_type = models.CharField(max_length=3,
                                     null=True,
                                     help_text="""Use breseq mutation codes, see the genome diff site
                                     on the barrick lab wiki (http://tinyurl.com/l3fvnap) for more
                                     information""")

    position = models.IntegerField()

    feature_length = models.IntegerField(blank=True,
                                         null=True)

    sequence_change = models.CharField(max_length=100)

    protein_change = models.CharField(max_length=300,
                                      blank=True,
                                      null=True)

    gene = models.CharField(max_length=300,
                            blank=True,
                            null=True)

    product = models.CharField(max_length=500, default="", null=True)

    function = models.CharField(max_length=500, default="", null=True)

    go_process = models.CharField(max_length=300, default="", null=True)

    go_component = models.CharField(max_length=300, default="", null=True)

    reseq_reference = models.CharField(max_length=200, **blank_field)

    # "reference_error" was created to indicate mutations that are generated only because
    # the reference isn't realistic and not because the organism is actually
    # different from the original strain. This is why setting this value to
    # true ignores enables further analysis to ignore these mutations.

    reference_error = models.NullBooleanField(default=False)

    def __unicode__(self):
        return u"%d %s" % (self.position,
                           self.sequence_change)


class ObservedMutation(models.Model):

    sequencing_experiment = models.ForeignKey(ResequencingExperiment)

    mutation = models.ForeignKey(Mutation)

    present = models.NullBooleanField()

    breseq_present = models.NullBooleanField()

    wt_reads = models.IntegerField(null=True)

    mutated_reads = models.IntegerField(null=True)

    other_reads = models.IntegerField(null=True)

    reference_genome_likelihood = models.FloatField(null=True)

    evidence = models.CharField(max_length=400,
                                blank=True,
                                null=True)

    frequency = models.DecimalField(null=True,
                                    max_digits=5,
                                    decimal_places=4)


