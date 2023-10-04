from django.db import models
from genes.util import get_gene_list
from seq.util import get_ecocyc_gene_list
from django.utils.safestring import mark_safe

blank_field = {"blank": True, "null": True}


# TODO: Refactor: figure out how to get a ResequencingExperiment to return its list of observed mutations and remove functionality from seq.views.common
class ResequencingExperiment(models.Model):
    tech_rep = models.ForeignKey("ale.TechnicalReplicate", on_delete=models.CASCADE,
                                 null=True)
    person = models.CharField(max_length=200,
                              blank=True)
    reads = models.IntegerField(blank=True,
                                default=0)
    average_read_length = models.FloatField(blank=True,
                                            default=0)
    mutations = models.ManyToManyField("Mutation",
                                       through="ObservedMutation")
    location = models.CharField(max_length=200,
                                blank=True,
                                null=True)
    experiment_location = models.CharField(max_length=200,
                                blank=True,
                                null=True)
    gatk_location = models.CharField(max_length=200,
                                blank=True,
                                null=True)
    sample_name = models.CharField(max_length=200,
                                blank=True,
                                null=True)
    mean_coverage = models.FloatField(blank=True,
                                      default=0)
    percentage_mapped = models.FloatField(blank=True,
                                          default=0)

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
    def exp_ale_flask_isolate_str(self):
        return self.ale_experiment.name + " " + self.ale_flask_isolate_str


class UnassignedMissingCoverageEvidence(models.Model):
    reads_left_url = models.CharField(max_length=500, **blank_field)
    reads_right_url = models.CharField(max_length=500, **blank_field)
    coverage = models.CharField(max_length=500, **blank_field)
    seq_id = models.CharField(max_length=100)
    start = models.CharField(max_length=100)
    end = models.CharField(max_length=100)
    size = models.CharField(max_length=200)
    reads_left = models.CharField(max_length=100, **blank_field)
    reads_right = models.CharField(max_length=100, **blank_field)
    gene = models.CharField(max_length=50, **blank_field)
    description = models.CharField(max_length=500, **blank_field)
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
    sequence_change = models.CharField(max_length=200)
    protein_change = models.CharField(max_length=300,
                                      default="")
    gene = models.CharField(max_length=19000, blank=True, null=True)  # TODO: use TextField for this.
    product = models.TextField(default="", null=True)
    function = models.CharField(max_length=500, default="", null=True)
    go_process = models.CharField(max_length=300, default="", null=True)
    go_component = models.CharField(max_length=300, default="", null=True)
    reseq_reference = models.CharField(max_length=200, **blank_field)
    tags = models.CharField(max_length=500, **blank_field)

    # "reference_error" was created to indicate mutations that are generated only because
    # the reference isn't realistic and not because the organism is actually
    # different from the original strain. This is why setting this value to
    # true ignores enables further analysis to ignore these mutations.

    reference_error = models.NullBooleanField(default=False)

    def __unicode__(self):
        return u"%d %s" % (self.position,
                           self.sequence_change)

    def is_ecocyc_gene(self) -> bool:
        return self.reseq_reference == 'NC_000913'

    def ecocyc_gene_urls(self) -> str:
        """
        get gene links string for table cell display
        :return: gene links for display in mutation table
        """
        return mark_safe(", ".join(get_ecocyc_gene_list(get_gene_list(self.gene), self.is_ecocyc_gene())))


class ObservedMutation(models.Model):
    sequencing_experiment = models.ForeignKey(ResequencingExperiment, on_delete=models.CASCADE, null=True)
    # make sure not delete mutation if there is associated observed mutations
    mutation = models.ForeignKey(Mutation, on_delete=models.DO_NOTHING)
    present = models.NullBooleanField()
    breseq_present = models.NullBooleanField()
    gatk_present = models.NullBooleanField()
    wt_reads = models.IntegerField(null=True)
    mutated_reads = models.IntegerField(null=True)
    other_reads = models.IntegerField(null=True)
    reference_genome_likelihood = models.FloatField(null=True)
    evidence = models.CharField(max_length=400,
                                blank=True,
                                null=True)
    gatk_evidence = models.CharField(max_length=400,
                                     blank=True,
                                     null=True)
    frequency = models.DecimalField(null=True,
                                    max_digits=5,
                                    decimal_places=4)
    frequency_gatk = models.DecimalField(null=True,
                                         max_digits=5,
                                         decimal_places=4)

    def get_experiment_id(self):
        return self.sequencing_experiment.tech_rep.isolate.flask.ale_id.ale_experiment_id

