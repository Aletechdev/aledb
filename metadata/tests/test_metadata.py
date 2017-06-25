from django.test import TestCase
from ale.models import AleExperiment,\
    Instrument,\
    Isolate,\
    TechnicalReplicate,\
    Media,\
    Flask,\
    AleId,\
    FreezerBox
from metadata.parser import parse_metadata_post_experiment_upload
import os


ALE_EXP_PRIMARY_EXP = 1  # I'm assuming will always be 1 due to rebuild of DB with the unit testing.

__author__ = 'Patrick Phaneuf'


class TestParser(TestCase):

    def setUp(self):
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

    def test_metadata_two_tech_reps_cant_change_media(self):
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
        parse_metadata_post_experiment_upload(path + "test3/", ALE_EXP_PRIMARY_EXP)
        self.assertEqual(3, Media.objects.all().count())
        tech_rep_queryset = TechnicalReplicate.objects.all()
        self.assertEqual(2, tech_rep_queryset.count())
        for tech_rep in tech_rep_queryset:
            substrate = tech_rep.isolate.flask.media.substrate
            expected_substrate = "Glucose(4)"  # Will be Glucose even though tried to change tech_rep_2 to Acetate(4)
            try:
                self.assertEqual(expected_substrate, substrate)
            except AssertionError as e:
                print("Failed with:", substrate, "tech_rep_number " + str(tech_rep.tech_rep_number))
                raise e

        first_tech_rep = tech_rep_queryset.filter(isolate__flask__ale_id__ale_id=7,
                                                  isolate__flask__flask_number=90,
                                                  isolate__isolate_number=0,
                                                  tech_rep_number=1)
        self.assertEqual("Glucose(4)", first_tech_rep[0].isolate.flask.media.substrate)

    # def test_metadata_two_tech_reps_change_media(self):
    #     media = Media.objects.create(substrate="nothing")
    #     ale_id = AleId.objects.create(ale_experiment=self.ale_exp,
    #                                   ale_id=7)
    #     flask = Flask.objects.create(media=media,
    #                                  ale_id=ale_id,
    #                                  flask_number=90)
    #     isolate = Isolate.objects.create(flask=flask,
    #                                      isolate_number=0,
    #                                      is_population=False,
    #                                      freezer_box=self.freezerbox)
    #     TechnicalReplicate.objects.create(isolate=isolate,
    #                                       tech_rep_number=1)
    #     TechnicalReplicate.objects.create(isolate=isolate,
    #                                       tech_rep_number=2)
    #
    #     path = os.path.dirname(os.path.realpath(__file__)) + "/"
    #     parse_metadata_post_experiment_upload(path + "test3/", ALE_EXP_PRIMARY_EXP)
    #     self.assertEqual(3, Media.objects.all().count())
    #     tech_rep_queryset = TechnicalReplicate.objects.all()
    #     self.assertEqual(2, tech_rep_queryset.count())
    #     for tech_rep in tech_rep_queryset:
    #         substrate = tech_rep.isolate.flask.media.substrate
    #         expected_substrate = ""
    #         if tech_rep.tech_rep_number == 1:
    #             expected_substrate = "Glucose(4)"
    #         if tech_rep.tech_rep_number == 2:
    #             expected_substrate = "Acetate(4)"
    #         try:
    #             self.assertEqual(expected_substrate, substrate)
    #         except AssertionError as e:
    #             print("Failed with:", substrate, "tech_rep_number " + str(tech_rep.tech_rep_number))
    #             raise e
    #
    #     first_tech_rep = tech_rep_queryset.filter(isolate__flask__ale_id__ale_id=7,
    #                                               isolate__flask__flask_number=90,
    #                                               isolate__isolate_number=0,
    #                                               tech_rep_number=1)
    #     self.assertEqual("Glucose(4)", first_tech_rep[0].isolate.flask.media.substrate)