from django.test import TestCase
from seq.models import Mutation, ObservedMutation, ResequencingExperiment
from enrichment import enrichment
from filter.models import AleExperimentFilter, GlobalFilter
from ale.models import \
    AleExperiment,\
    Instrument,\
    AleId,\
    Flask,\
    Media,\
    FreezerBox,\
    Isolate,\
    TechnicalReplicate


__author__ = 'Patrick Phaneuf'


class TestEnrichment(TestCase):

    def setUp(self):
        self.ale_exp = AleExperiment.objects.create(instrument=Instrument.objects.create())
        self.ale = AleId.objects.create(ale_id=1, ale_experiment=self.ale_exp)
        self.media = Media.objects.create()
        self.freezer_box = FreezerBox.objects.create()
        self.flask = Flask.objects.create(flask_number=1,
                                      ale_id=self.ale, media=self.media)
        self.isolate = Isolate.objects.create(flask=self.flask,
                                         isolate_number=1, is_population=False, freezer_box=self.freezer_box)
        self.tech_rep = TechnicalReplicate.objects.create(isolate=self.isolate)
        self.reseq = ResequencingExperiment.objects.create(tech_rep=self.tech_rep)


    def test_enriched_geneA_same_mutation_queryset(self):

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        frequency=1,
                                        mutation=mut,)

        mut = Mutation.objects.create(mutation_type="asd",
                                      position=1,
                                      sequence_change="gfds",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        frequency=1,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="yui",
                                      position=1,
                                      sequence_change="hjkl",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        frequency=1,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=2,
                                      sequence_change="zxcv",
                                      gene="geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        frequency=1,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="asd",
                                      position=2,
                                      sequence_change="gfds",
                                      gene="geneD")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        frequency=1,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="yui",
                                      position=2,
                                      sequence_change="hjkl",
                                      gene="geneF")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        frequency=1,
                                        mutation=mut)

        # Need queryset for this test.
        mutation_pos1_queryset = ObservedMutation.objects.filter(mutation__position=1)
        mutation_pos2_queryset = ObservedMutation.objects.filter(mutation__position=2)
        enrichment_mutation_list = enrichment.get_enrichment_mutation_list([mutation_pos1_queryset, mutation_pos2_queryset])
        expected_enriched_gene = "geneA"
        for mutation in enrichment_mutation_list:
            self.assertEquals(expected_enriched_gene, mutation.gene)

    def test_enriched_geneA_diff_mutation_queryset(self):
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        frequency=1,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="asd",
                                       position=1,
                                       sequence_change="gfds",
                                       gene="geneW")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        frequency=1,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="yui",
                                       position=1,
                                       sequence_change="hjkl",
                                       gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        frequency=1,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="qwe",
                                       position=2,
                                       sequence_change="zxcv",
                                       gene="geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        frequency=1,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="asd",
                                       position=2,
                                       sequence_change="gfds",
                                       gene="geneD")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        frequency=1,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="yui",
                                       position=2,
                                       sequence_change="hjkl",
                                       gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        frequency=1,
                                        mutation=mut)

        # Need queryset for this test.
        mutation_pos1_queryset = ObservedMutation.objects.filter(mutation__position=1)
        mutation_pos2_queryset = ObservedMutation.objects.filter(mutation__position=2)
        enrichment_mutation_list = enrichment.get_enrichment_mutation_list([mutation_pos1_queryset, mutation_pos2_queryset])
        expected_enriched_gene = "geneB"
        for mutation in enrichment_mutation_list:
            self.assertEquals(expected_enriched_gene, mutation.gene)

    def test_enrichment_with_diff_gene_annotation(self):
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="seq_chng1",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="seq_chng1",
                                      gene="[geneA]")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        observed_mutation_queryset = ObservedMutation.objects.all()
        enrichment_mutation_list = enrichment.get_enrichment_mutation_list([observed_mutation_queryset])

        self.assertTrue(len(enrichment_mutation_list) == 2)
        for enrichment_mutation in enrichment_mutation_list:
            self.assertTrue("geneA" in enrichment_mutation.gene)

    def test_dont_add_same_enriched_mutation_twice(self):
        mut = Mutation.objects.create(gene="geneA",
                                      mutation_type="SNP", position=1, sequence_change="seq_chng_1")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq, mutation=mut, frequency=1)

        mut = Mutation.objects.create(gene="geneA, geneB",
                                      mutation_type="SNP",
                                      position=1,
                                      sequence_change="seq_chng_2")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(gene="geneB",
                                      mutation_type="SNP",
                                      position=1,
                                      sequence_change="seq_chng_3")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        # Need queryset for this test.
        observed_mutation_queryset = ObservedMutation.objects.all()
        enrichment_mutation_list = enrichment.get_enrichment_mutation_list([observed_mutation_queryset])

        self.assertEquals(3, len(enrichment_mutation_list))
