from django.test import TestCase
from seq.models import Mutation
from enrichment.util import Enrichment

__author__ = 'Patrick Phaneuf'


class TestEnrichment(TestCase):

    def test_enriched_geneA_same_mutation_queryset(self):
        mut1 = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="geneA")
        mut1.save()

        mut2 = Mutation.objects.create(mutation_type="asd",
                                       position=1,
                                       sequence_change="gfds",
                                       gene="geneA")
        mut2.save()

        mut3 = Mutation.objects.create(mutation_type="yui",
                                       position=1,
                                       sequence_change="hjkl",
                                       gene="geneB")
        mut3.save()

        mut1 = Mutation.objects.create(mutation_type="qwe",
                                       position=2,
                                       sequence_change="zxcv",
                                       gene="geneC")
        mut1.save()

        mut2 = Mutation.objects.create(mutation_type="asd",
                                       position=2,
                                       sequence_change="gfds",
                                       gene="geneD")
        mut2.save()

        mut3 = Mutation.objects.create(mutation_type="yui",
                                       position=2,
                                       sequence_change="hjkl",
                                       gene="geneF")
        mut3.save()

        mutation_pos1_queryset = Mutation.objects.filter(position=1)
        mutation_pos2_queryset = Mutation.objects.filter(position=2)
        enrichment = Enrichment([mutation_pos1_queryset, mutation_pos2_queryset])
        expected_enriched_gene = "geneA"
        for mutation in enrichment.enrichment_mutation_list:
            self.assertEquals(expected_enriched_gene, mutation.gene)


    def test_enriched_geneA_diff_mutation_queryset(self):
        mut1 = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="geneA")
        mut1.save()

        mut2 = Mutation.objects.create(mutation_type="asd",
                                       position=1,
                                       sequence_change="gfds",
                                       gene="geneW")
        mut2.save()

        mut3 = Mutation.objects.create(mutation_type="yui",
                                       position=1,
                                       sequence_change="hjkl",
                                       gene="geneB")
        mut3.save()

        mut1 = Mutation.objects.create(mutation_type="qwe",
                                       position=2,
                                       sequence_change="zxcv",
                                       gene="geneC")
        mut1.save()

        mut2 = Mutation.objects.create(mutation_type="asd",
                                       position=2,
                                       sequence_change="gfds",
                                       gene="geneD")
        mut2.save()

        mut3 = Mutation.objects.create(mutation_type="yui",
                                       position=2,
                                       sequence_change="hjkl",
                                       gene="geneB")
        mut3.save()

        mutation_pos1_queryset = Mutation.objects.filter(position=1)
        mutation_pos2_queryset = Mutation.objects.filter(position=2)
        enrichment = Enrichment([mutation_pos1_queryset, mutation_pos2_queryset])
        expected_enriched_gene = "geneB"
        for mutation in enrichment.enrichment_mutation_list:
            self.assertEquals(expected_enriched_gene, mutation.gene)

    def test_dont_add_same_enriched_mutation_twice(self):
        mut = Mutation.objects.create(mutation_type="qwe",
                                       position=1,
                                       sequence_change="seq_chng1",
                                       gene="geneA")
        mut.save()

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="seq_chng2",
                                      gene="geneA, geneB")
        mut.save()

        mut = Mutation.objects.create(mutation_type="qwe",
                                       position=1,
                                       sequence_change="seq_chng3",
                                       gene="geneB")
        mut.save()

        mutation_queryset = Mutation.objects.all()
        enrichment = Enrichment([mutation_queryset])

        self.assertEquals(3, len(enrichment.enrichment_mutation_list))