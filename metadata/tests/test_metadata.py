from django.test import TestCase
from django.contrib.auth.models import User
from ale.models import AleExperiment,\
    Instrument,\
    Isolate,\
    TechnicalReplicate,\
    Media,\
    Flask,\
    AleId,\
    FreezerBox,\
    Project
from metadata.parser import parse_metadata_post_experiment_upload, _get_media_supplement_description
from datetime import datetime
import os
from metadata.xpmdvalidator.validate import is_valid
import csv

ALE_EXP_PRIMARY_EXP = 1  # I'm assuming will always be 1 due to rebuild of DB with the unit testing.

__author__ = 'Patrick Phaneuf'


class TestParser(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="Troy", password="test123",
                                        first_name="Troy", last_name="Sandberg", email="email@email.com",
                                        is_active=True, is_staff=True, date_joined=datetime.now())
        self.project = Project.objects.create(name="SSW Glu Ac", user = self.user)
        self.instrument = Instrument.objects.create()
        self.freezerbox = FreezerBox.objects.create()
        self.ale_exp = AleExperiment.objects.create(instrument=self.instrument)

    def test_metadata_change(self):
        media = Media.objects.create(substrate="nothing")
        ale_id = AleId.objects.create(ale_experiment=self.ale_exp,
                                      ale_id=7)
        flask = Flask.objects.create(media=media,
                                     ale_id=ale_id,
                                     flask_number=90)
        isolate = Isolate.objects.create(flask=flask,
                                         isolate_number=0,
                                         is_population=False,
                                         freezer_box=self.freezerbox)
        TechnicalReplicate.objects.create(isolate=isolate,
                                          tech_rep_number=1)

        path = os.path.dirname(os.path.realpath(__file__)) + "/"
        parse_metadata_post_experiment_upload(path + "test1/", ALE_EXP_PRIMARY_EXP)
        self.assertEqual(2, Media.objects.all().count())
        tech_rep_queryset = TechnicalReplicate.objects.all()
        self.assertEqual(1, tech_rep_queryset.count())
        test1_media = tech_rep_queryset[0].isolate.flask.media.substrate
        self.assertEquals(test1_media, "Glucose(4)")

        # Tries to change the media of the same tech_rep.isolate.flask.
        parse_metadata_post_experiment_upload(path + "test2/", ALE_EXP_PRIMARY_EXP)
        self.assertEqual(3, Media.objects.all().count())
        tech_rep_queryset = TechnicalReplicate.objects.all()
        self.assertEqual(1, len(tech_rep_queryset))
        test2_media = tech_rep_queryset[0].isolate.flask.media.substrate
        self.assertEquals(test2_media, "Acetate(4)")

    def test_get_media_supplement_description(self):
        path = os.path.dirname(os.path.realpath(__file__)) + "/"
        metadata_path = path + "test3/"
        for f in os.listdir(metadata_path):
            if f.endswith(".csv") or f.endswith(".CSV"):
                with open(os.path.join(metadata_path, f), 'rt') as csvfile:
                    metadata_dict = dict(csv.reader(csvfile, delimiter=','))
            self.assertRegexpMatches(_get_media_supplement_description(metadata_dict), r'^.* Pimelic acid\(21\)$')

    def test_creating_media_with_metadata_upload(self):
        media = Media.objects.create(substrate="nothing")
        ale_id = AleId.objects.create(ale_experiment=self.ale_exp,
                                      ale_id=7)
        flask = Flask.objects.create(media=media,
                                     ale_id=ale_id,
                                     flask_number=90)
        isolate = Isolate.objects.create(flask=flask,
                                         isolate_number=0,
                                         is_population=False,
                                         freezer_box=self.freezerbox)
        TechnicalReplicate.objects.create(isolate=isolate,
                                          tech_rep_number=1)
        TechnicalReplicate.objects.create(isolate=isolate,
                                          tech_rep_number=2)
        # The metadata uploading should be creating 2 different types of media.
        path = os.path.dirname(os.path.realpath(__file__)) + "/"
        parse_metadata_post_experiment_upload(path + "test3/", ALE_EXP_PRIMARY_EXP)
        media_queryset = Media.objects.all()
        print("here")
        print(media_queryset[0].description)
        media_present_dict = {"nothing": False, "Glucose(4)": False, "Acetate(4)": False}
        for media in media_queryset:
            media_present_dict[media.substrate] = True
        for media_present_value in media_present_dict.values():
            self.assertEqual(True, media_present_value)

    def test_reuse_media_with_metadata_upload(self):
        media = Media.objects.create(substrate="nothing")
        ale_id = AleId.objects.create(ale_experiment=self.ale_exp,
                                      ale_id=7)
        flask = Flask.objects.create(media=media,
                                     ale_id=ale_id,
                                     flask_number=90)
        isolate = Isolate.objects.create(flask=flask,
                                         isolate_number=0,
                                         is_population=False,
                                         freezer_box=self.freezerbox)
        TechnicalReplicate.objects.create(isolate=isolate,
                                          tech_rep_number=1)
        TechnicalReplicate.objects.create(isolate=isolate,
                                          tech_rep_number=2)
        path = os.path.dirname(os.path.realpath(__file__)) + "/"
        parse_metadata_post_experiment_upload(path + "test_reuse_media_with_metadata_upload/", ALE_EXP_PRIMARY_EXP)
        media_queryset = Media.objects.all()
        media_present_dict = {"nothing": 0, "Glucose(4)": 0}
        for media in media_queryset:
            media_present_dict[media.substrate] += 1
        for media_name, media_count in media_present_dict.items():
            expected_count = 0
            if media_name == "nothing":
                expected_count = 1
            if media_name == "Glucose(4)":
                expected_count = 1
            self.assertEqual(expected_count, media_count)

    # Only way to change foreign key flask media is to change the media and save this change
    def test_metadata_two_tech_reps_change_media(self):
        media = Media.objects.create(substrate="nothing")
        ale_id = AleId.objects.create(ale_experiment=self.ale_exp,
                                      ale_id=7)
        flask = Flask.objects.create(media=media,
                                     ale_id=ale_id,
                                     flask_number=90)
        isolate = Isolate.objects.create(flask=flask,
                                         isolate_number=0,
                                         is_population=False,
                                         freezer_box=self.freezerbox)
        TechnicalReplicate.objects.create(isolate=isolate,
                                          tech_rep_number=1)
        TechnicalReplicate.objects.create(isolate=isolate,
                                          tech_rep_number=2)

        path = os.path.dirname(os.path.realpath(__file__)) + "/"

        # Will populate all tech_reps to have Glucose(4) substrate, even though 7-90-0-1 only being set.
        parse_metadata_post_experiment_upload(path + "test1/", ALE_EXP_PRIMARY_EXP)
        tech_rep_queryset = TechnicalReplicate.objects.all()
        self.assertEqual(2, tech_rep_queryset.count())
        for tech_rep in tech_rep_queryset:
            self.assertEqual("Glucose(4)", tech_rep.isolate.flask.media.substrate)

        parse_metadata_post_experiment_upload(path + "7-90-0-2_acetate/", ALE_EXP_PRIMARY_EXP)
        tech_rep_queryset = TechnicalReplicate.objects.all()
        self.assertEqual(2, tech_rep_queryset.count())
        for tech_rep in tech_rep_queryset:
            self.assertEqual("Acetate(4)", tech_rep.isolate.flask.media.substrate)

    def test_xpmd_validator(self):
        path = os.path.dirname(os.path.realpath(__file__)) + "/"
        self.assertTrue(is_valid(path + "test1/", path + "../xpmdvalidator/Json_schema.json"))
        self.assertFalse(is_valid(path + "test_bad_metadata/", path + "../xpmdvalidator/Json_schema.json"))

