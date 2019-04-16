import os
from django.test import TestCase

from django.contrib.auth.models import User
from ale.models import Project
from datetime import datetime
from bibliome.models import Publication
from bibliome.publication import create_publication
from builder.ale_experiment import create_ale_experiment

__author__ = 'Muyao'


class TestBibliome(TestCase):

    def test_create_publication(self):
        self.current_location = os.path.dirname(os.path.realpath(__file__))
        self.user = User.objects.create(username="pphaneuf", password="test123",
                                        first_name="Patrick", last_name="Phaneuf", email="email@email.com",
                                        is_active=True, is_staff=True, date_joined=datetime.now())
        Project.objects.create(name="test_project", user=self.user, date=datetime.now(),
                               status="In progress", is_public=False)
        test_report_path = os.path.dirname(os.path.realpath(__file__)) + "/../../builder/tests/breseq/"
        create_ale_experiment(test_report_path, "Patrick", "test", "test_project")
        expected_publication_count = 1
        create_publication("test_publication_journal", "aledb.org", 1)
        self.assertEqual(expected_publication_count, Publication.objects.all().count())
