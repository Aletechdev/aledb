from django.test import TestCase
from seq.models import Mutation, ObservedMutation, ResequencingExperiment
from converge import converge
from filter.models import AleExperimentFilter, GlobalFilter
from ale.models import \
    AleExperiment, \
    Instrument, \
    AleId, \
    Flask, \
    Media, \
    FreezerBox, \
    Isolate, \
    TechnicalReplicate

__author__ = 'Patrick Phaneuf'


# TODO: each test should first test to see that the enrichment set isn't empty. If it is, the test will still pass.
class TestCoverage(TestCase):

    def setUp(self):
        self.ale_exp = AleExperiment.objects.create(instrument=Instrument.objects.create())
        self.media = Media.objects.create()
        self.freezer_box = FreezerBox.objects.create()

    def test_only_geneA_converges(self):
        ale_1 = AleId.objects.create(ale_id=1, ale_experiment=self.ale_exp)
        ale_2 = AleId.objects.create(ale_id=2, ale_experiment=self.ale_exp)

        ale1_flask = Flask.objects.create(flask_number=1,
                                          ale_id=ale_1,
                                          media=self.media)
        ale2_flask1 = Flask.objects.create(flask_number=1,
                                          ale_id=ale_2,
                                          media=self.media)
        ale2_flask2 = Flask.objects.create(flask_number=2,
                                           ale_id=ale_2,
                                           media=self.media)

        ale1_isolate = Isolate.objects.create(flask=ale1_flask,
                                              isolate_number=1,
                                              is_population=False,
                                              freezer_box=self.freezer_box)
        ale2_isolate1 = Isolate.objects.create(flask=ale2_flask1,
                                              isolate_number=1,
                                              is_population=False,
                                              freezer_box=self.freezer_box)
        ale2_isolate2 = Isolate.objects.create(flask=ale2_flask2,
                                              isolate_number=1,
                                              is_population=False,
                                              freezer_box=self.freezer_box)

        ale1_tech_rep = TechnicalReplicate.objects.create(isolate=ale1_isolate)
        ale2_tech_rep1 = TechnicalReplicate.objects.create(isolate=ale2_isolate1)
        ale2_tech_rep2 = TechnicalReplicate.objects.create(isolate=ale2_isolate2)

        ale1_reseq = ResequencingExperiment.objects.create(tech_rep=ale1_tech_rep)
        ale2_reseq1 = ResequencingExperiment.objects.create(tech_rep=ale2_tech_rep1)
        ale2_reseq2 = ResequencingExperiment.objects.create(tech_rep=ale2_tech_rep2)

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=ale1_reseq,
                                        frequency=1,
                                        mutation=mut)


        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=ale2_reseq1,
                                        frequency=1,
                                        mutation=mut)

        mut = Mutation.objects.create(mutation_type="djg",
                                      position=1,
                                      sequence_change="qwer",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=ale2_reseq2,
                                        frequency=1,
                                        mutation=mut, )

        mut = Mutation.objects.create(mutation_type="cvb",
                                      position=1,
                                      sequence_change="sdfg",
                                      gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=ale2_reseq2,
                                        frequency=1,
                                        mutation=mut, )

        obs_mut_qryset = ObservedMutation.objects.all()
        converge_mut_list = converge.get_converge_mutation_list([obs_mut_qryset])
        expected_converged_gene = "geneA"
        for mutation in converge_mut_list:
            self.assertEquals(expected_converged_gene , mutation.gene)