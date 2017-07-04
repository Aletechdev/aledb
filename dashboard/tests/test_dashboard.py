from django.test import TestCase
from dashboard.util import rebuild_sample_counts
from dashboard.models import SampleCounts
from ale.models import AleExperiment, Instrument, AleId


class TestDashboard(TestCase):
    def test_rebuild_sample_counts(self):
        ale_exp = AleExperiment.objects.create(instrument=Instrument.objects.create())
        AleId.objects.create(ale_experiment=ale_exp, ale_id=0)
        AleId.objects.create(ale_experiment=ale_exp, ale_id=9)
        AleId.objects.create(ale_experiment=ale_exp, ale_id=24)
        AleId.objects.create(ale_experiment=ale_exp, ale_id=1)
        rebuild_sample_counts()
        expected_ale_count = 3
        self.assertEqual(SampleCounts.objects.all()[0].ale_count, expected_ale_count)
