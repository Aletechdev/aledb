import os

import csv

from ale.models import TechnicalReplicate
from ale.models import Media


__author__ = 'Denny Gosting, Patrick Phaneuf'

DEFAULT_INSTRUMENT_NAME = ""
DEFAULT_MEDIA_DESCRIPTION = "M9"
DEFAULT_MEDIA_SUBSTRATE = "glucose"
DEFAULT_TEMPERATURE = 37
DEFAULT_VOLUME = 15
DEFAULT_STIRRING_SPEED = 1100
DEFAULT_FREEZER_BOX_NAME = "ALE box"
DEFAULT_FREEZER_BOX_NUMBER = 1

STRAIN = "taxonomy-id"
STRAIN_DESCRIPTION = "strain-description"
MEDIA_BASE_DESCRIPTION = "base-media"
MEDIA_CARBON_SOURCE = "carbon-source"
MEDIA_NITROGEN_SOURCE = "nitrogen-source"
MEDIA_PHOSPHOROUS_SOURCE = "phosphorous-source"
MEDIA_SULFUR_SOURCE = "Sulfur-source"
MEDIA_ELECTRON_ACCEPTOR = "electron-acceptor"
MEDIA_SUPPLEMENT = "supplement"
MEDIA_ANTIBIOTIC = "antibiotic"
MEDIA_TEMPERATURE = "temperature"
LIBRARY_PREP_KIT_MANUFACTURER = "library-prep-kit-manufacturer"
LIBRARY_PREP_KIT_CYCLES = "library-prep-kit-cycles"
ALE_NUMBER = "ALE-number"
FLASK_NUMBER = "Flask-number"
ISOLATE_NUMBER = "Isolate-number"
TECH_REP_NUMBER = "technical-replicate-number"

DEFAULT_STRAIN = "E. Coli"
DEFAULT_DESCRIPTION = ""


def _get_media_substrate_description(metadata_dict):

    if MEDIA_CARBON_SOURCE in metadata_dict.keys():
        media_substrate_description = metadata_dict[MEDIA_CARBON_SOURCE]
        if media_substrate_description == "":
            media_substrate_description = DEFAULT_MEDIA_SUBSTRATE
    else:
        media_substrate_description = DEFAULT_MEDIA_SUBSTRATE

    if MEDIA_CARBON_SOURCE in metadata_dict.keys():
        media_substrate_description += " " + \
            metadata_dict[MEDIA_NITROGEN_SOURCE]
    if MEDIA_PHOSPHOROUS_SOURCE in metadata_dict.keys():
        media_substrate_description += " " + \
            metadata_dict[MEDIA_PHOSPHOROUS_SOURCE]
    if MEDIA_SULFUR_SOURCE in metadata_dict.keys():
        media_substrate_description += " " + metadata_dict[MEDIA_SULFUR_SOURCE]
    if MEDIA_ELECTRON_ACCEPTOR in metadata_dict.keys():
        media_substrate_description += " " + \
            metadata_dict[MEDIA_ELECTRON_ACCEPTOR]
    if MEDIA_ELECTRON_ACCEPTOR in metadata_dict.keys():
        media_substrate_description += " " + \
            metadata_dict[MEDIA_ELECTRON_ACCEPTOR]
    if MEDIA_SUPPLEMENT in metadata_dict.keys():
        media_substrate_description += " " + metadata_dict[MEDIA_SUPPLEMENT]

    return media_substrate_description


def parse_metadata_post_experiment_upload(meta_data_path, ale_experiment_primary_key):

    for f in os.listdir(meta_data_path):

        if f.endswith(".csv") or f.endswith(".CSV"):

            with open(os.path.join(meta_data_path, f), 'rt') as csvfile:
                metadata_dict = dict(csv.reader(csvfile, delimiter=','))

                try:
                    tech_rep = TechnicalReplicate.objects.get(
                        tech_rep_number=metadata_dict[TECH_REP_NUMBER],
                        isolate__isolate_number=metadata_dict[ISOLATE_NUMBER],
                        isolate__flask__flask_number=metadata_dict[FLASK_NUMBER],
                        isolate__flask__ale_id__ale_id=metadata_dict[ALE_NUMBER],
                        isolate__flask__ale_id__ale_experiment__ale_id=ale_experiment_primary_key)
                except Exception as e:
                    print("Error for " + metadata_dict[ALE_NUMBER] + "-" + metadata_dict[FLASK_NUMBER] + "-" + metadata_dict[ISOLATE_NUMBER] + '-' + metadata_dict[TECH_REP_NUMBER] + ": ", e)
                    continue

                try:
                    ale_id_description = metadata_dict[STRAIN_DESCRIPTION]
                except:
                    ale_id_description = DEFAULT_DESCRIPTION

                try:
                    strain = metadata_dict[STRAIN]
                except:
                    strain = DEFAULT_DESCRIPTION

                try:
                    library_prep = metadata_dict[LIBRARY_PREP_KIT_MANUFACTURER] + \
                        "/ " + metadata_dict[LIBRARY_PREP_KIT_CYCLES]
                    if library_prep is "/ ":
                        library_prep = DEFAULT_DESCRIPTION
                except:
                    library_prep = DEFAULT_DESCRIPTION

                try:
                    media_description = metadata_dict[MEDIA_BASE_DESCRIPTION]
                except:
                    media_description = DEFAULT_MEDIA_DESCRIPTION

                try:
                    media_temperature = metadata_dict[MEDIA_TEMPERATURE]
                    if media_temperature is '':
                        media_temperature = DEFAULT_TEMPERATURE
                except:
                    media_temperature = DEFAULT_TEMPERATURE

                media_substrate_description = _get_media_substrate_description(
                    metadata_dict)

                media, created = Media.objects.get_or_create(description=media_description,
                                                             substrate=media_substrate_description,
                                                             temperature=media_temperature,
                                                             volume=DEFAULT_VOLUME,
                                                             stirring_speed=DEFAULT_STIRRING_SPEED)
                tech_rep.isolate.flask.media = media

                tech_rep.isolate.flask.ale_id.description = ale_id_description
                tech_rep.isolate.flask.ale_id.strain = strain
                tech_rep.isolate.library_prep = library_prep

                if tech_rep.isolate.flask.ale_id.species is None:
                    tech_rep.isolate.flask.ale_id.species = DEFAULT_STRAIN

                tech_rep.isolate.flask.ale_id.save()

                tech_rep.isolate.flask.media.save()
                tech_rep.isolate.flask.save()
                tech_rep.isolate.save()
                tech_rep.save()
