from django.test import TestCase
from dashboard.util import rebuild_sample_counts
from dashboard.models import SampleCounts
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

    def test_rebuild_sample_counts_filter_starting_strain_isolate(self):
        freezer_box = FreezerBox.objects.create()
        ale_exp = AleExperiment.objects.create(instrument=Instrument.objects.create())
        ale_id = AleId.objects.create(ale_experiment=ale_exp, ale_id=2)
        flask = Flask.objects.create(media=Media.objects.create(), ale_id=ale_id)
        Isolate.objects.create(freezer_box=freezer_box, flask=flask, is_population=False, isolate_number=0)
        Isolate.objects.create(freezer_box=freezer_box, flask=flask, is_population=False, isolate_number=1)
        Isolate.objects.create(freezer_box=freezer_box, flask=flask, is_population=False, isolate_number=2)
        rebuild_sample_counts()
        expected_count = 2
        self.assertEqual(SampleCounts.objects.all()[0].isolate_count, expected_count)

