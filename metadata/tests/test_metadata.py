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

        tech_rep_queryset = TechnicalReplicate.objects.all()
        path = os.path.dirname(os.path.realpath(__file__)) + "/"
        parse_metadata_post_experiment_upload(path + "test1/", ALE_EXP_PRIMARY_EXP)
        test1_media = tech_rep_queryset[0].isolate.flask.media.substrate
        self.assertEquals(test1_media, "Glucose(4)")
        parse_metadata_post_experiment_upload(path + "test2/", ALE_EXP_PRIMARY_EXP)
        test2_media = tech_rep_queryset[0].isolate.flask.media.substrate
        self.assertEquals(test2_media, "Acetate(4)")

    def test_metadata_two_tech_reps(self):
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

        tech_rep_queryset = TechnicalReplicate.objects.all()

        path = os.path.dirname(os.path.realpath(__file__)) + "/"
        parse_metadata_post_experiment_upload(path + "test3/", ALE_EXP_PRIMARY_EXP)

        for tech_rep in tech_rep_queryset:
            substrate = tech_rep.isolate.flask.media.substrate
            expected_substrate = ""
            afir = self._get_afir(tech_rep)
            if afir == [7,90,0,1]:
                expected_substrate = "Acetate(4)"
            elif afir == [7,90,0,2]:
                expected_substrate = "Glucose(4)"
            try:
                self.assertEqual(substrate, expected_substrate)
            except AssertionError as e:
                print(afir)
                raise e

    def _get_afir(self, tech_rep):
        afir_list=[]
        afir_list.append(tech_rep.isolate.flask.ale_id.ale_id)
        afir_list.append(tech_rep.isolate.flask.flask_number)
        afir_list.append(tech_rep.isolate.isolate_number)
        afir_list.append(tech_rep.tech_rep_number)
        return afir_list