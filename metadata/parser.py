import os

import csv

from ale.models import Isolate

__author__ = 'dgosting'

STRAIN = "taxonomy-id"
DESCRIPTION = "strain-description"
MEDIA = "base-media"
TEMPERATURE = "environment"
LIBRARY_PREP_KIT_MANUFACTURER = "library-prep-kit-manufacturer"
LIBRARY_PREP_KIT_CYCLES = "library-prep-kit-cycles"
ALE_NUMBER = "ALE-number"
FLASK_NUMBER = "Flask-number"
ISOLATE_NUMBER = "Isolate-number"

DEFAULT_STRAIN = "E. Coli"


def parse_and_upload_meta_data(meta_data_path, ale_experiment_primary_key):

    for f in os.listdir(meta_data_path):

        if f.endswith(".csv"):

            with open(os.path.join(meta_data_path, f), 'rt') as csvfile:

                meta_data = dict(csv.reader(csvfile, delimiter=','))

                isolate = Isolate.objects.get(isolate_number=meta_data[ISOLATE_NUMBER],
                                              flask__flask_number=meta_data[FLASK_NUMBER],
                                              flask__ale_id__ale_id=meta_data[ALE_NUMBER],
                                              flask__ale_id__ale_experiment__ale_id=ale_experiment_primary_key)

                isolate.flask.media.temperature = meta_data[TEMPERATURE].replace("C", "")
                isolate.flask.ale_id.description = meta_data[DESCRIPTION]
                isolate.flask.ale_id.strain = meta_data[STRAIN]
                isolate.library_prep = meta_data[LIBRARY_PREP_KIT_MANUFACTURER] + "/ " + meta_data[LIBRARY_PREP_KIT_CYCLES]
                isolate.flask.media.description = meta_data[MEDIA]

                if isolate.flask.ale_id.species is None:
                    isolate.flask.ale_id.species = DEFAULT_STRAIN

                isolate.save()
                isolate.flask.media.save()
                isolate.flask.ale_id.save()
