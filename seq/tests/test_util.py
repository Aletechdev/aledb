from django.test import TestCase
from seq.models import Mutation, ObservedMutation, ResequencingExperiment

__author__ = 'Patrick Phaneuf'


class TestEnrichment(TestCase):

    def setUp(self):
        # TODO: figure out a way not to have to create a default reseq_exp
        self.reseq = ResequencingExperiment.objects.create()
    #
    #     # TODO: had to do this to make filter_settings object. Find cleaner way.
    #     self.ale_exp = AleExperiment.objects.create(instrument=Instrument.objects.create())

    def test(self):
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="asd",
                                      position=1,
                                      sequence_change="gfds",
                                      gene="geneB, geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut)

        observed_mutation_queryset = ObservedMutation.objects.all()
        gene_list = ["geneA", "geneC"]
        asdf = observed_mutation_queryset.filter(mutation__gene__in=gene_list).count()
        print(asdf)

    def itertools_test(self):
        a = [1, 2, 1, 1, 2, 1, 2, 2, 3, 3, 4, 5, 5]
        from itertools import groupby
        print([len(list(group)) for key, group in groupby(a)])

