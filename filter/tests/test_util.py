from django.test import TestCase
from seq.models import Mutation
from seq.models import ObservedMutation
from seq.models import ResequencingExperiment
from filter.models import AleExperimentFilter, GlobalFilter
from ale.models import TechnicalReplicate,\
    Isolate,\
    Flask,\
    AleId,\
    AleExperiment,\
    Media,\
    FreezerBox
from ale.models import Instrument
from filter.util import filter_observed_mutations, get_filter_settings_queryset_from_observed_mutations


__author__ = 'Patrick Phaneuf'


class TestEnrichment(TestCase):

    def test_mutation_filter_one_gene_mutation_and_filter(self):
        reseq = ResequencingExperiment.objects.create()
        ale_exp = AleExperiment.objects.create(instrument=Instrument.objects.create())
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=reseq,
                                        mutation=mut,
                                        frequency=1)

        filter_settings = AleExperimentFilter.objects.create(ale_experiment=ale_exp, ignored_genes="geneA")
        obs_mut_queryset = filter_observed_mutations(ObservedMutation.objects.all(), filter_settings)
        self.assertEquals(len(obs_mut_queryset), 0)

    def test_mutation_filter_one_gene_mutation_many_gene_filter(self):
        reseq = ResequencingExperiment.objects.create()
        ale_exp = AleExperiment.objects.create(instrument=Instrument.objects.create())
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="rcsF")
        ObservedMutation.objects.create(sequencing_experiment=reseq,
                                        mutation=mut,
                                        frequency=1)

        filter_settings = AleExperimentFilter.objects.create(ale_experiment=ale_exp,
                                                             ignored_genes="rcsF, –/–, rrlH, rrlD, rrsH, rrlA, gltP/yjcO, rsxC, eco/mqo")
        obs_mut_queryset = filter_observed_mutations(ObservedMutation.objects.all(), filter_settings)
        self.assertEquals(len(obs_mut_queryset), 0)

    def test_mutation_filter_many_gene_mutation_one_gene_filter(self):
        reseq = ResequencingExperiment.objects.create()
        ale_exp = AleExperiment.objects.create(instrument=Instrument.objects.create())
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="geneA, geneB")
        ObservedMutation.objects.create(sequencing_experiment=reseq,
                                        mutation=mut,
                                        frequency=1)

        filter_settings = AleExperimentFilter.objects.create(ale_experiment=ale_exp,
                                                             ignored_genes="geneA")

        obs_mut_queryset = filter_observed_mutations(ObservedMutation.objects.all(), filter_settings)
        self.assertEquals(len(obs_mut_queryset), 1)

    def test_mutation_filter_many_gene_mutation_many_gene_filter(self):
        reseq = ResequencingExperiment.objects.create()
        ale_exp = AleExperiment.objects.create(instrument=Instrument.objects.create())
        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="geneA, geneB")
        ObservedMutation.objects.create(sequencing_experiment=reseq,
                                        mutation=mut,
                                        frequency=1)

        filter_settings = AleExperimentFilter.objects.create(ale_experiment=ale_exp,
                                                             ignored_genes="geneB, geneA")

        obs_mut_queryset = filter_observed_mutations(ObservedMutation.objects.all(), filter_settings)
        self.assertEquals(len(obs_mut_queryset), 0)

    def test_get_filter_settings_queryset_from_observed_mutations(self):
        ale_exp = AleExperiment.objects.create(name="exp1",
                                               instrument=Instrument.objects.create())
        AleExperimentFilter.objects.create(ale_experiment=ale_exp, ignored_genes="geneA")
        ale = AleId.objects.create(ale_id=1,
                                   ale_experiment=ale_exp)
        media = Media.objects.create()
        flask = Flask.objects.create(ale_id=ale, media=media)
        freezer_box = FreezerBox.objects.create()
        isolate = Isolate.objects.create(flask=flask,
                                         isolate_number=1,
                                         is_population=False,
                                         freezer_box=freezer_box)
        tech_rep = TechnicalReplicate.objects.create(isolate=isolate,)
        reseq = ResequencingExperiment.objects.create(tech_rep=tech_rep)
        mut = Mutation.objects.create(mutation_type="SNP",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=reseq,
                                        mutation=mut,
                                        frequency=1)

        obs_mut_qryset = ObservedMutation.objects.all()
        ale_exp_filter_settings_qryset = get_filter_settings_queryset_from_observed_mutations(obs_mut_qryset)
        self.assertEqual(ale_exp_filter_settings_qryset[0].ignored_genes, "geneA")