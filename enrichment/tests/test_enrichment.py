from django.test import TestCase
from seq.models import Mutation
from seq.models import ObservedMutation
from seq.models import ResequencingExperiment
from enrichment.util import Enrichment
from filter.models import AleExperimentFilter
from filter.models import GlobalFilter
from ale.models import AleExperiment
from ale.models import Instrument

__author__ = 'Patrick Phaneuf'


class TestEnrichment(TestCase):

    def setUp(self):
        # TODO: figure out a way not to have to create a default reseq_exp
        self.reseq = ResequencingExperiment.objects.create()

        # TODO: had to do this to make filter_settings object. Find cleaner way.
        self.ale_exp = AleExperiment.objects.create(
            instrument=Instrument.objects.create())

    def test_enriched_geneA_same_mutation_queryset(self):

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="asd",
                                      position=1,
                                      sequence_change="gfds",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="yui",
                                      position=1,
                                      sequence_change="hjkl",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=2,
                                      sequence_change="zxcv",
                                      gene="geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="asd",
                                      position=2,
                                      sequence_change="gfds",
                                      gene="geneD")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="yui",
                                      position=2,
                                      sequence_change="hjkl",
                                      gene="geneF")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut)

        # Need queryset for this test.
        mutation_pos1_queryset = ObservedMutation.objects.filter(mutation__position=1)
        mutation_pos2_queryset = ObservedMutation.objects.filter(mutation__position=2)
        enrichment = Enrichment([mutation_pos1_queryset, mutation_pos2_queryset])
        expected_enriched_gene = "geneA"
        for mutation in enrichment.enrichment_mutation_list:
            self.assertEquals(expected_enriched_gene, mutation.gene)

    def test_enriched_geneA_diff_mutation_queryset(self):
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="asd",
                                       position=1,
                                       sequence_change="gfds",
                                       gene="geneW")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="yui",
                                       position=1,
                                       sequence_change="hjkl",
                                       gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="qwe",
                                       position=2,
                                       sequence_change="zxcv",
                                       gene="geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="asd",
                                       position=2,
                                       sequence_change="gfds",
                                       gene="geneD")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="yui",
                                       position=2,
                                       sequence_change="hjkl",
                                       gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut)

        # Need queryset for this test.
        mutation_pos1_queryset = ObservedMutation.objects.filter(mutation__position=1)
        mutation_pos2_queryset = ObservedMutation.objects.filter(mutation__position=2)
        enrichment = Enrichment([mutation_pos1_queryset, mutation_pos2_queryset])
        expected_enriched_gene = "geneB"
        for mutation in enrichment.enrichment_mutation_list:
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
        enrichment = Enrichment([observed_mutation_queryset])

        self.assertTrue(len(enrichment.enrichment_mutation_list) == 2)
        for enrichment_mutation in enrichment.enrichment_mutation_list:
            self.assertTrue("geneA" in enrichment_mutation.gene)

    def test_dont_add_same_enriched_mutation_twice(self):
        # TODO: figure out a way not to have to create a default reseq_exp
        test_reseq_exp = ResequencingExperiment.objects.create()
        mut = Mutation.objects.create(mutation_type="qwe",
                                       position=1,
                                       sequence_change="seq_chng1",
                                       gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="seq_chng2",
                                      gene="geneA, geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                       position=1,
                                       sequence_change="seq_chng3",
                                       gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        # Need queryset for this test.
        observed_mutation_queryset = ObservedMutation.objects.all()
        enrichment = Enrichment([observed_mutation_queryset])

        self.assertEquals(3, len(enrichment.enrichment_mutation_list))

    # TODO: all ignore tests should likely be reproduced in unit tests in the filter project since they apply to functionality using mutations.
    def test_ignore_genes(self):

        # Will ignore this mutation due to singular gene.
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        # Won't ignore this mutation, though won't consider geneA enriched,
        # therefore no enrichment mutations.
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA, geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        filter_settings = AleExperimentFilter.objects.create(ale_experiment=self.ale_exp, ignored_genes="geneA")

        observed_mutation_queryset = ObservedMutation.objects.all()
        enrichment = Enrichment(reseq_obs_mut_list=[observed_mutation_queryset], filter_settings=filter_settings)

        self.assertTrue(len(enrichment.enrichment_mutation_list) == 2)

        expected_enriched_gene = "geneC"
        for returned_enrichment_mutations in enrichment.enrichment_mutation_list:
            self.assertEquals(returned_enrichment_mutations.gene, expected_enriched_gene)

    def test_ignore_genes_with_annotation(self):
        # Will ignore this mutation due to singular gene.
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        # Won't ignore this mutation, though won't consider geneA enriched,
        # therefore no enrichment mutations.
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="[geneA], geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="[geneA]")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        filter_settings = AleExperimentFilter.objects.create(ale_experiment=self.ale_exp, ignored_genes="geneA")

        observed_mutation_queryset = ObservedMutation.objects.all()
        enrichment = Enrichment(reseq_obs_mut_list=[observed_mutation_queryset],
                                filter_settings=filter_settings)

        self.assertEquals(len(enrichment.enrichment_mutation_list), 0)

    def test_ignore_starting_strain_mutations(self):
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        filter_settings = AleExperimentFilter.objects.create(ale_experiment=self.ale_exp,
                                                             starting_strain_mutations="1")

        observed_mutation_queryset = ObservedMutation.objects.all()
        enrichment = Enrichment(reseq_obs_mut_list=[observed_mutation_queryset], filter_settings=filter_settings)

        self.assertTrue(len(enrichment.enrichment_mutation_list) == 2)

        expected_enriched_gene = "geneB"
        for returned_enrichment_mutations in enrichment.enrichment_mutation_list:
            self.assertEquals(returned_enrichment_mutations.gene, expected_enriched_gene)

    def test_ignore_multiple_starting_strain_mutations(self):
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        filter_settings = AleExperimentFilter.objects.create(ale_experiment=self.ale_exp,
                                                             starting_strain_mutations="2,3")

        observed_mutation_queryset = ObservedMutation.objects.all()
        enrichment = Enrichment(reseq_obs_mut_list=[observed_mutation_queryset], filter_settings=filter_settings)

        self.assertTrue(len(enrichment.enrichment_mutation_list) == 2)

        expected_enriched_gene = "geneC"
        for returned_enrichment_mutations in enrichment.enrichment_mutation_list:
            self.assertEquals(returned_enrichment_mutations.gene, expected_enriched_gene)

    def test_dont_ignore_mutation_with_gene_list(self):
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA, geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        filter_settings = AleExperimentFilter.objects.create(ale_experiment=self.ale_exp, ignored_genes="geneB")
        observed_mutation_queryset = ObservedMutation.objects.all()
        enrichment = Enrichment(reseq_obs_mut_list=[observed_mutation_queryset],
                                filter_settings=filter_settings)

        self.assertTrue(len(enrichment.enrichment_mutation_list) == 2)
        for enrichment_mutation in enrichment.enrichment_mutation_list:
            self.assertTrue("geneA" in enrichment_mutation.gene)

    def test_ignore_mutation_id(self):
        # This test relies on the fact that the id's given to the mutations
        # by the DB tech start at 1 and increment by 1.

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        # This mutation will be given a mutation.id of 2.
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        filter_settings = AleExperimentFilter.objects.create(ale_experiment=self.ale_exp,
                                                             ignored_mutations='2')

        observed_mutation_queryset = ObservedMutation.objects.all()
        enrichment = Enrichment(reseq_obs_mut_list=[observed_mutation_queryset],
                                filter_settings=filter_settings)

        self.assertTrue(len(enrichment.enrichment_mutation_list) == 2)
        for enrichment_mutation in enrichment.enrichment_mutation_list:
            self.assertTrue("geneB" in enrichment_mutation.gene)

    def test_ignore_multiple_mutation_id(self):
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        filter_settings = AleExperimentFilter.objects.create(ale_experiment=self.ale_exp,
                                                             ignored_mutations='2,3')

        observed_mutation_queryset = ObservedMutation.objects.all()
        enrichment = Enrichment(reseq_obs_mut_list=[observed_mutation_queryset],
                                filter_settings=filter_settings)

        self.assertTrue(len(enrichment.enrichment_mutation_list) == 2)
        for enrichment_mutation in enrichment.enrichment_mutation_list:
            self.assertTrue("geneC" in enrichment_mutation.gene)

    def test_using_both_ignore_mutation_id_and_gene(self):
        # Will ignore this mutation according to ignore gene list.
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        # Will ignore this mutation according to ignore gene list.
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        # Will ignore this mutation according to ignore mutation id list.
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        # geneC won't register as enriched since the other geneC mutation is ignored.
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneD, geneE")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneD")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        filter_settings = AleExperimentFilter.objects.create(ale_experiment=self.ale_exp,
                                                             ignored_genes="geneA",
                                                             ignored_mutations='3')

        observed_mutation_queryset = ObservedMutation.objects.all()
        enrichment = Enrichment(reseq_obs_mut_list=[observed_mutation_queryset],
                                filter_settings=filter_settings)

        self.assertTrue(len(enrichment.enrichment_mutation_list) == 2)
        for enrichment_mutation in enrichment.enrichment_mutation_list:
            self.assertTrue("geneD" in enrichment_mutation.gene)

    def test_ignore_mutation_gene_list_full_ignore_list(self):
        # Will ignore this mutation according to ignore gene list.
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB, geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        # Will ignore this mutation according to ignore gene list.
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        observed_mutation_queryset = ObservedMutation.objects.all()
        filter_settings = AleExperimentFilter.objects.create(ale_experiment=self.ale_exp,
                                                             ignored_genes="geneA, geneB")
        enrichment = Enrichment(reseq_obs_mut_list=[observed_mutation_queryset],
                                filter_settings=filter_settings)

        self.assertTrue(len(enrichment.enrichment_mutation_list) == 2)
        for enrichment_mutation in enrichment.enrichment_mutation_list:
            self.assertTrue("geneC" in enrichment_mutation.gene)

    def test_ignore_mutation_gene_list_not_full_ignore_list(self):

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB, geneA, geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        # Will ignore this mutation according to ignore gene list.
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        observed_mutation_queryset = ObservedMutation.objects.all()
        filter_settings = AleExperimentFilter.objects.create(ale_experiment=self.ale_exp,
                                                             ignored_genes="geneA, geneB")
        enrichment = Enrichment(reseq_obs_mut_list=[observed_mutation_queryset],
                                filter_settings=filter_settings)

        self.assertTrue(len(enrichment.enrichment_mutation_list) == 2)

    def test_ignore_mutation_on_low_freq(self):
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=0.1)

        # Will ignore this mutation according to ignore gene list.
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=0.25)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=0.25)

        observed_mutation_queryset = ObservedMutation.objects.all()
        filter_settings = AleExperimentFilter.objects.create(ale_experiment=self.ale_exp,
                                                             min_cutoff=20)
        enrichment = Enrichment(reseq_obs_mut_list=[observed_mutation_queryset],
                                filter_settings=filter_settings)

        self.assertTrue(len(enrichment.enrichment_mutation_list) == 2)
        for enrichment_mutation in enrichment.enrichment_mutation_list:
            self.assertTrue("geneB" in enrichment_mutation.gene)

    def test_ignore_global_gene_only(self):
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        # Will ignore this mutation according to ignore gene list.
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        observed_mutation_queryset = ObservedMutation.objects.all()
        GlobalFilter.objects.create(ignored_genes="geneA")
        enrichment = Enrichment(reseq_obs_mut_list=[observed_mutation_queryset])

        self.assertTrue(len(enrichment.enrichment_mutation_list) == 2)
        for enrichment_mutation in enrichment.enrichment_mutation_list:
            self.assertTrue("geneB" in enrichment_mutation.gene)

    def test_ignore_global_mutation_only(self):
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        observed_mutation_queryset = ObservedMutation.objects.all()
        GlobalFilter.objects.create(ignored_mutations="1")
        enrichment = Enrichment(reseq_obs_mut_list=[observed_mutation_queryset])

        self.assertTrue(len(enrichment.enrichment_mutation_list) == 2)
        for enrichment_mutation in enrichment.enrichment_mutation_list:
            self.assertTrue("geneB" in enrichment_mutation.gene)

    def test_ignore_multiple_global_mutation_only(self):
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneC")
        ObservedMutation.objects.create(sequencing_experiment=self.reseq,
                                        mutation=mut,
                                        frequency=1)

        observed_mutation_queryset = ObservedMutation.objects.all()
        GlobalFilter.objects.create(ignored_mutations="1,3")
        enrichment = Enrichment(reseq_obs_mut_list=[observed_mutation_queryset])

        self.assertTrue(len(enrichment.enrichment_mutation_list) == 2)
        for enrichment_mutation in enrichment.enrichment_mutation_list:
            self.assertTrue("geneC" in enrichment_mutation.gene)