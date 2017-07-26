from django.test import TestCase
from dashboard.models import ObservedMutationCounts, UniqueMutationCounts
from builder.ale_experiment import rebuild_dashboard_data, create_ale_experiment
import os


class TestEnrichment(TestCase):

    def test_rebuild_counts_only_builds_one(self):
        self.assertEqual(ObservedMutationCounts.objects.count(), 0)
        self.assertEqual(UniqueMutationCounts.objects.count(), 0)
        rebuild_dashboard_data()
        self.assertEqual(ObservedMutationCounts.objects.count(), 1)
        self.assertEqual(UniqueMutationCounts.objects.count(), 1)
        rebuild_dashboard_data()
        self.assertEqual(ObservedMutationCounts.objects.count(), 1)
        self.assertEqual(UniqueMutationCounts.objects.count(), 1)

    def test_create_ALE_experiment(self):
        test_report_path = os.path.dirname(os.path.realpath(__file__))+"/breseq/"
        create_ale_experiment(test_report_path, "Patrick", "test")
        # pass if no crashing or freezing.