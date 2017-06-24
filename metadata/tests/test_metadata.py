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
    # 1) create ALE, flask, isolate, and tech_rep
    # 2) load metadata for tech_rep
    # test the subtrate of the query path.
    # 3) load different metadata for tech_rep
    def test_metadata_change(self):
        media = Media.objects.create()
        instrument = Instrument.objects.create()
        freezer_box = FreezerBox.objects.create()
        ale_exp = AleExperiment.objects.create(instrument=instrument)
        ale_id = AleId.objects.create(ale_experiment=ale_exp,
                                      ale_id=7)
        flask = Flask.objects.create(media=media,
                                     ale_id=ale_id,
                                     flask_number=90)
        isolate = Isolate.objects.create(flask=flask,
                                         isolate_number=0,
                                         is_population=False,
                                         freezer_box=freezer_box)
        tech_rep = TechnicalReplicate.objects.create(isolate=isolate,
                                                     tech_rep_number=1)

        tech_rep_queryset = TechnicalReplicate.objects.filter(tech_rep_number=1,
                                                              isolate__isolate_number=0,
                                                              isolate__flask__flask_number=90,
                                                              isolate__flask__ale_id__ale_id=7)

        path = os.path.dirname(os.path.realpath(__file__)) + "/"
        parse_metadata_post_experiment_upload(path + "test1/", ALE_EXP_PRIMARY_EXP)

        test1_media = tech_rep_queryset[0].isolate.flask.media.substrate
        test1_media = test1_media.strip(' ')
        self.assertEquals(test1_media, "Glucose(4)")

        parse_metadata_post_experiment_upload(path + "test2/", ALE_EXP_PRIMARY_EXP)
        test1_media = tech_rep_queryset[0].isolate.flask.media.substrate
        test1_media = test1_media.strip(' ')
        self.assertEquals(test1_media, "Acetate(4)")