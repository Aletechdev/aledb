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
DEFAULT_TEMPERATURE = 37

def parse_and_upload_meta_data(meta_data_path, ale_experiment_primary_key):

    for f in os.listdir(meta_data_path):

        if f.endswith(".csv"):

            with open(os.path.join(meta_data_path, f), 'rt') as csvfile:

                meta_data = dict(csv.reader(csvfile, delimiter=','))

                try:
                    isolate = Isolate.objects.get(isolate_number=meta_data[ISOLATE_NUMBER],
                                                  flask__flask_number=meta_data[FLASK_NUMBER],
                                                  flask__ale_id__ale_id=meta_data[ALE_NUMBER],
                                                  flask__ale_id__ale_experiment__ale_id=ale_experiment_primary_key)
                except Exception as e:
                    print("Error for " + meta_data[ALE_NUMBER] + "-" + meta_data[FLASK_NUMBER] + "-" + meta_data[ISOLATE_NUMBER] + ": ", e)
                    continue

                try:
                    temp = meta_data[TEMPERATURE].replace("C", "")
                    if meta_data[TEMPERATURE] is '':
                        temp = DEFAULT_TEMPERATURE
                except:
                    temp = DEFAULT_TEMPERATURE

                try:
                    ale_id_description = meta_data[DESCRIPTION]
                except:
                    ale_id_description = ""

                try:
                    strain = meta_data[STRAIN]
                except:
                    strain = ""

                try:
                    library_prep = meta_data[LIBRARY_PREP_KIT_MANUFACTURER] + "/ " + meta_data[LIBRARY_PREP_KIT_CYCLES]
                    if library_prep is "/ ":
                        library_prep = ""
                except:
                    library_prep = ""

                try:
                    media_description = meta_data[MEDIA]
                except:
                    media_description = ""

                isolate.flask.media.temperature = temp
                isolate.flask.ale_id.description = ale_id_description
                isolate.flask.ale_id.strain = strain
                isolate.library_prep = library_prep
                isolate.flask.media.description = media_description

                if isolate.flask.ale_id.species is None:
                    isolate.flask.ale_id.species = DEFAULT_STRAIN

                isolate.save()
                isolate.flask.media.save()
                isolate.flask.ale_id.save()
