from django.test import TestCase
from dashboard.util import rebuild_sample_counts
from dashboard.models import SampleCounts, BarCharts
from ale.models import AleExperiment, Instrument, AleId, Flask, Media, Isolate, FreezerBox


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

    def test_bar_charts(self):
        gene_bar_chart_dict = [{"rpo": 2}, {"crr": 5}]
        BarCharts.objects.create(mut_gene_json=gene_bar_chart_dict)
        print(BarCharts.objects.all()[0].mut_gene_json)
