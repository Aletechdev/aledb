from django.test import TestCase
from django.db import transaction
from django.contrib.auth.models import User

from stats.models import StaticData
from ale.models import Project, AleExperiment
from seq.models import Mutation, ResequencingExperiment
from builder.ale_experiment import find_user, create_ale_experiment, try_creating_project, find_experiment_paths, \
    upload_ale_collection, upload_ale_experiment
from datetime import datetime
import os
import sys
import io

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
        self.user = User.objects.create(username="pphaneuf", password="test123",
                                        first_name="Patrick", last_name="Phaneuf", email="email@email.com",
                                        is_active = True, is_staff = True, date_joined = datetime.now())
        Project.objects.create(name="test_project", user=self.user, date=datetime.now(),
        status = "In progress", is_public = False)

    def test_create_ALE_experiment(self):
        test_report_path = os.path.dirname(os.path.realpath(__file__)) + "/breseq/"
        create_ale_experiment(test_report_path, "Patrick", "test", "test_project")
        expected_mutation_count = 27
        self.assertEqual(expected_mutation_count, Mutation.objects.all().count())
        expected_experiment_count = 1
        self.assertEqual(expected_experiment_count, AleExperiment.objects.all().count())
        expected_histogram_length = 68
        self.assertEquals(expected_histogram_length, len(StaticData.objects.get(id=1).histogram_data))

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

    def test_find_user(self):
        self.assertEquals(self.user, find_user("pphaneuf"))
        self.assertEquals(self.user, find_user("Patrick"))
        f1 = sys.stdin
        f = io.StringIO('patrick')
        sys.stdin = f
        self.assertEquals(self.user, find_user("Krusty Krab"))
        f.close()
        sys.stdin = f1

    def test_try_creating_project(self):
        patrick = self.user
        try_creating_project("Created Project", "Patrick Phaneuf", is_pub=False)
        created_project = Project.objects.get(name="Created Project")
        self.assertEquals(created_project.name, "Created Project")
        self.assertEquals(created_project.user, patrick)
        expected_project_count = 2
        self.assertEquals(expected_project_count, Project.objects.all().count())

    def test_find_experiment_paths(self):
        self.assertEquals(find_experiment_paths(os.path.dirname(os.path.realpath(__file__))).sort(),
                          ['/app/builder/tests/test_file_structure',
                           '/app/builder/tests/test_file_structure/messy'].sort())

