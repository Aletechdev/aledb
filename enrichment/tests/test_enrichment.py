from django.test import TestCase
from seq.models import Mutation
from enrichment.enrichment import Enrichment

__author__ = 'Patrick Phaneuf'


class TestEnrichment(TestCase):

    def test_enriched_geneA(self):
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

        mutation_queryset = Mutation.objects.all()
        enrichment = Enrichment([mutation_queryset])
        expected_enriched_gene = "geneA"
        for mutation in enrichment.enrichment_mutation_list:
            self.assertEquals(expected_enriched_gene, mutation.gene)