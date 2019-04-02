from django.test import TestCase
from django.contrib.auth.models import User
from seq.models import Mutation, ResequencingExperiment
from builder.ale_experiment import rebuild_dashboard_data, create_ale_experiment
from datetime import datetime
import os


class TestEnrichment(TestCase):
    # TODO: the unit test below no longer works: need to find out why.
    """
    def test_rebuild_counts_only_builds_one(self):
        self.assertEqual(ObservedMutationCounts.objects.count(), 0)
        self.assertEqual(UniqueMutationCounts.objects.count(), 0)
        rebuild_dashboard_data()
        self.assertEqual(ObservedMutationCounts.objects.count(), 1)
        self.assertEqual(UniqueMutationCounts.objects.count(), 1)
        rebuild_dashboard_data()
        self.assertEqual(ObservedMutationCounts.objects.count(), 1)
        self.assertEqual(UniqueMutationCounts.objects.count(), 1)
    """

    def setUp(self):
        print("Creating test user Patrick")
        User.objects.create(username="Patrick", password="test123",
                            first_name="Patrick", last_name="Phaneuf", email="email@email.com",
                            is_active=True, is_staff=True, date_joined=datetime.now())

    def test_create_ALE_experiment(self):
        test_report_path = os.path.dirname(os.path.realpath(__file__)) + "/breseq/"
        create_ale_experiment(test_report_path, "Patrick", "test", "test_project")
        expected_mutation_count = 27
        self.assertEqual(expected_mutation_count, Mutation.objects.all().count())

    def test_reseq_URL(self):
        test_report_path = os.path.dirname(os.path.realpath(__file__)) + "/test_reseq_url/"
        create_ale_experiment(test_report_path, "Patrick", "test", "test_project")
        reseq_qryset = ResequencingExperiment.objects.all()
        empty_count = 0
        not_empty_count = 0
        for reseq in reseq_qryset:
            if reseq.location == "":
                empty_count += 1
            if "3-72-1-1" in reseq.location:
                not_empty_count += 1
        self.assertEqual(empty_count, 1)
        self.assertEqual(not_empty_count, 1)
