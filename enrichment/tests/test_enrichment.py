from django.test import TestCase
from seq.models import Mutation

__author__ = 'Patrick Phaneuf'


class TestEnrichment(TestCase):

    def test_Enrichment(self):
        mut1 = Mutation.objects.create(mutation_type="SNP",
                                      position=1,
                                      sequence_change="delta776 bp",
                                      gene="geneA")
        mut1.save()

        mut2 = Mutation.objects.create(mutation_type="qwe",
                                       position=2,
                                       sequence_change="asdfasdf",
                                       gene="geneB")
        mut2.save()

        mutation_queryset = Mutation.objects.all()
        for mutation in mutation_queryset:
            print(mutation.sequence_change)
        self.assertTrue(True)