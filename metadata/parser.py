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
LIBRARY_PREP_KIT_MANUFACTURER = "library-prep-kit-manufacturer"
LIBRARY_PREP_KIT_CYCLES = "library-prep-kit-cycles"
ALE_NUMBER = "ALE-number"
FLASK_NUMBER = "Flask-number"
ISOLATE_NUMBER = "Isolate-number"
TECH_REP_NUMBER = "technical-replicate-number"
EXPERIMENT_DETAILS = "experiment-details"

DEFAULT_STRAIN = "E. Coli"

MEDIA_BASE_DESCRIPTION = "base-media"
MEDIA_TEMPERATURE = "temperature"
#  The following media descriptors are consolidated into the ALEdb "substrate" descriptor.
MEDIA_CARBON_SOURCE = "carbon-source"
MEDIA_NITROGEN_SOURCE = "nitrogen-source"
MEDIA_PHOSPHOROUS_SOURCE = "phosphorous-source"
MEDIA_SULFUR_SOURCE = "Sulfur-source"
MEDIA_ELECTRON_ACCEPTOR = "electron-acceptor"
MEDIA_SUPPLEMENT = "supplement"
MEDIA_ANTIBIOTIC = "antibiotic"
MEDIA_DESCRIPTOR_LIST = [MEDIA_CARBON_SOURCE,
                         MEDIA_NITROGEN_SOURCE,
                         MEDIA_PHOSPHOROUS_SOURCE,
                         MEDIA_PHOSPHOROUS_SOURCE,
                         MEDIA_SULFUR_SOURCE,
                         MEDIA_ELECTRON_ACCEPTOR,
                         MEDIA_SUPPLEMENT,
                         MEDIA_ANTIBIOTIC]


def _get_media_substrate_description(metadata_dict):
    media_substrate_description = ''
    for media_descriptor in MEDIA_DESCRIPTOR_LIST:
        if media_descriptor in metadata_dict.keys() and metadata_dict[media_descriptor] != '':
            media_substrate_description += metadata_dict[media_descriptor]

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

            ale_id_description = ""
            if STRAIN_DESCRIPTION in metadata_dict.keys():
                ale_id_description = metadata_dict[STRAIN_DESCRIPTION]

            strain = ""
            if STRAIN in metadata_dict.keys():
                strain = metadata_dict[STRAIN]

            media_description = ""
            if MEDIA_BASE_DESCRIPTION in metadata_dict.keys():
                media_description = metadata_dict[MEDIA_BASE_DESCRIPTION]

            library_prep = ""
            if LIBRARY_PREP_KIT_MANUFACTURER in metadata_dict.keys():
                library_prep = metadata_dict[LIBRARY_PREP_KIT_MANUFACTURER]
            if LIBRARY_PREP_KIT_CYCLES in metadata_dict.keys():
                if library_prep != "":
                    library_prep += "/ "
                library_prep += metadata_dict[LIBRARY_PREP_KIT_CYCLES]

            media_temperature = DEFAULT_TEMPERATURE
            if MEDIA_TEMPERATURE in metadata_dict.keys() and metadata_dict[MEDIA_TEMPERATURE] != "":
                media_temperature = int(metadata_dict[MEDIA_TEMPERATURE])

            experiment_details = ""
            if EXPERIMENT_DETAILS in metadata_dict.keys():
                experiment_details = metadata_dict[EXPERIMENT_DETAILS]

            media_substrate_description = _get_media_substrate_description(metadata_dict)

            ale_id = tech_rep.isolate.flask.ale_id
            ale_id.description = ale_id_description
            ale_id.strain = strain
            if ale_id.species is None: ale_id.species = DEFAULT_STRAIN
            ale_id.save()

            media, created = Media.objects.get_or_create(description=media_description,
                                                         substrate=media_substrate_description,
                                                         temperature=media_temperature,
                                                         volume=DEFAULT_VOLUME,
                                                         stirring_speed=DEFAULT_STIRRING_SPEED)

            flask = tech_rep.isolate.flask
            flask.media = media
            flask.save()

            isolate = tech_rep.isolate
            isolate.library_prep = library_prep
            isolate.save()

            tech_rep.description = experiment_details
            tech_rep.save()
