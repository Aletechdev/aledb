from django.test import TestCase
from seq.models import Mutation
from seq.models import ObservedMutation
from seq.models import ResequencingExperiment
from filter.models import AleExperimentFilter
from filter.models import GlobalFilter
from ale.models import AleExperiment
from ale.models import Instrument
from filter.util import filter_observed_mutations

__author__ = 'Patrick Phaneuf'


class TestEnrichment(TestCase):

    def setUp(self):
        # TODO: figure out a way not to have to create a default reseq_exp
        self.reseq = ResequencingExperiment.objects.create()

        # TODO: had to do this to make filter_settings object. Find cleaner way.
        self.ale_exp = AleExperiment.objects.create(instrument=Instrument.objects.create())

    def test_mutation_filter_one_gene_mutation_and_filter(self):
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        filter_settings = AleExperimentFilter.objects.create(ale_experiment=self.ale_exp, ignored_genes="geneA")
        obs_mut_queryset = filter_observed_mutations(ObservedMutation.objects.all(), filter_settings)
        self.assertEquals(len(obs_mut_queryset), 0)

    def test_mutation_filter_one_gene_mutation_many_gene_filter(self):
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="rcsF")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        filter_settings = AleExperimentFilter.objects.create(ale_experiment=self.ale_exp,
                                                             ignored_genes="rcsF, –/–, rrlH, rrlD, rrsH, rrlA, gltP/yjcO, rsxC, eco/mqo")
        obs_mut_queryset = filter_observed_mutations(ObservedMutation.objects.all(), filter_settings)
        self.assertEquals(len(obs_mut_queryset), 0)

    def test_mutation_filter_many_gene_mutation_one_gene_filter(self):
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="geneA, geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        filter_settings = AleExperimentFilter.objects.create(ale_experiment=self.ale_exp,
                                                             ignored_genes="geneA")

        obs_mut_queryset = filter_observed_mutations(ObservedMutation.objects.all(), filter_settings)
        self.assertEquals(len(obs_mut_queryset), 1)

    def test_mutation_filter_many_gene_mutation_many_gene_filter(self):
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="geneA, geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        filter_settings = AleExperimentFilter.objects.create(ale_experiment=self.ale_exp,
                                                             ignored_genes="geneB, geneA")

        obs_mut_queryset = filter_observed_mutations(ObservedMutation.objects.all(), filter_settings)
        self.assertEquals(len(obs_mut_queryset), 0)