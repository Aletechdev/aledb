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

    # TODO: change back to "isolate_name" to match other properties above.
    def get_isolate_name(self):

        if self.isolate.description is not None:

            if len(self.isolate.description) > 0:

                return self.isolate.description

        return u"A%d_F%d_I%d" % (self.ale_id,
                                 self.flask_number,
                                 self.isolate.isolate_number)

        # TODO - add more information


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


class GeneToPDBManager(models.Manager):

    def create_mapping(self, gene, pdb_id, rank):
        new_mapping = self.create(gene=gene, pdb_id=pdb_id, rank=rank)
        return new_mapping


class GeneToPDB(models.Model):

    objects = GeneToPDBManager()

    gene = models.CharField(max_length=50)
    pdb_id = models.CharField(max_length=4, null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True, default=100)

