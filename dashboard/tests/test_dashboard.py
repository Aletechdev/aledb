from django.test import TestCase
from dashboard.util import rebuild_sample_counts, rebuild_mut_histogram_data
from dashboard.models import SampleCounts, BarCharts
from ale.models import AleExperiment, Instrument, AleId, Flask, Media, Isolate, FreezerBox
from seq.models import ResequencingExperiment, Mutation, ObservedMutation


class TestDashboard(TestCase):
    def test_rebuild_sample_counts_filter_starting_strain_ale_id(self):
        ale_exp = AleExperiment.objects.create(instrument=Instrument.objects.create())
        AleId.objects.create(ale_experiment=ale_exp, ale_id=0)
        AleId.objects.create(ale_experiment=ale_exp, ale_id=9)
        AleId.objects.create(ale_experiment=ale_exp, ale_id=24)
        AleId.objects.create(ale_experiment=ale_exp, ale_id=1)
        rebuild_sample_counts()
        expected_ale_count = 3
        self.assertEqual(SampleCounts.objects.all()[0].ale_count, expected_ale_count)

    def test_rebuild_sample_counts_filter_starting_strain_flask(self):
        ale_exp = AleExperiment.objects.create(instrument=Instrument.objects.create())
        ale_id_starting_strain = AleId.objects.create(ale_experiment=ale_exp, ale_id=0)
        ale_id_other = AleId.objects.create(ale_experiment=ale_exp, ale_id=9)
        Flask.objects.create(media=Media.objects.create(), ale_id=ale_id_starting_strain)
        Flask.objects.create(media=Media.objects.create(), ale_id=ale_id_other)
        rebuild_sample_counts()
        expected_ale_count = 1
        self.assertEqual(SampleCounts.objects.all()[0].ale_count, expected_ale_count)

    def test_rebuild_sample_counts_filter_starting_strain_isolate(self):
        freezer_box = FreezerBox.objects.create()
        ale_exp = AleExperiment.objects.create(instrument=Instrument.objects.create())

        ale_id_starting_strain = AleId.objects.create(ale_experiment=ale_exp, ale_id=0)
        ale_id_other = AleId.objects.create(ale_experiment=ale_exp, ale_id=1)
        flask_starting_strain = Flask.objects.create(media=Media.objects.create(), ale_id=ale_id_starting_strain)
        flask_other = Flask.objects.create(media=Media.objects.create(), ale_id=ale_id_other)

        Isolate.objects.create(freezer_box=freezer_box, flask=flask_starting_strain, is_population=False,
                               isolate_number=0)
        Isolate.objects.create(freezer_box=freezer_box, flask=flask_other, is_population=False, isolate_number=1)
        Isolate.objects.create(freezer_box=freezer_box, flask=flask_other, is_population=False, isolate_number=2)
        rebuild_sample_counts()
        expected_count = 2
        self.assertEqual(SampleCounts.objects.all()[0].isolate_count, expected_count)

    def test_save_bar_chart_jsons(self):
        reseq = ResequencingExperiment.objects.create()

        mut = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="zxcv",
                                      protein_change="xcvb",
                                      gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=reseq,
                                        frequency=1,
                                        mutation=mut)

        rebuild_mut_histogram_data()
        histogram_data = BarCharts.objects.all()[0]
        self.assertEqual(histogram_data.mut_json[0]["mutation__protein_change"], "xcvb")
        self.assertEqual(histogram_data.mut_gene_json[0]["mutation__mutation_type"], "qwe")