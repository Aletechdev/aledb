import os
import re
import csv
import json

from ale.models import TechnicalReplicate
from ale.models import Media
from ale.models import Project
from metadata.xpmdvalidator.validate import is_valid

__author__ = 'Denny Gosting, Patrick Phaneuf, Muyao'

DEFAULT_INSTRUMENT_NAME = ""
DEFAULT_MEDIA_DESCRIPTION = "M9"
DEFAULT_MEDIA_SUBSTRATE = "glucose"
DEFAULT_TEMPERATURE = 37
DEFAULT_VOLUME = 15
DEFAULT_STIRRING_SPEED = 1100
DEFAULT_FREEZER_BOX_NAME = "ALE box"
DEFAULT_FREEZER_BOX_NUMBER = 1

PROJECT = "project"
OWNER = "owner"
EXPERIMENT_NAME = "experiment/subproject"

STRAIN = "taxonomy id"
STRAIN_DESCRIPTION = "starting strain"
LIBRARY_PREP_KIT_MANUFACTURER = "seqencing library prep kit manufacturer"
LIBRARY_PREP_KIT_CYCLES = "sequencing library prep kit cycles"
ALE_NUMBER = "A"
FLASK_NUMBER = "F"
ISOLATE_NUMBER = "I"
TECH_REP_NUMBER = "R"
EXPERIMENT_DETAILS = "medium description"

MEDIA_BASE_DESCRIPTION = "medium derived from"

ENVIRONMENTAL_CONDITIONS = "environmental conditions"
MEDIA_TEMPERATURE = "temp"
#  The following media descriptors are consolidated into the ALEdb "substrate" descriptor.
MEDIA_COMPONENTS = "media components"
MEDIA_CARBON_SOURCE = "carbon source"
MEDIA_NITROGEN_SOURCE = "nitrogen source"
MEDIA_PHOSPHOROUS_SOURCE = "phosphorus source"
MEDIA_SULFUR_SOURCE = "sulfur source"
MEDIA_ELECTRON_ACCEPTOR = "electron acceptor"
MEDIA_SUPPLEMENT = "supplement"
MEDIA_ANTIBIOTIC = "antibiotic"
MEDIA_DESCRIPTOR_LIST = [MEDIA_CARBON_SOURCE,
                         MEDIA_NITROGEN_SOURCE,
                         MEDIA_PHOSPHOROUS_SOURCE,
                         MEDIA_SULFUR_SOURCE,
                         MEDIA_ELECTRON_ACCEPTOR,
                         MEDIA_SUPPLEMENT,
                         MEDIA_ANTIBIOTIC]

def multiple_replace(text):
    word_dict = {
        ' ': "_"
    }
    for key in word_dict:
        text = text.replace(key, word_dict[key])
    text = re.sub(r'[^A-Za-z0-9_-]+', '', text)
    return text

def extract_experiment_parameters(metadata_path):
    # need to ensure all the csv files give the same parameters
    project = "N/A"
    creator = "N/A"
    experiment = "N/A"

    for f in os.listdir(metadata_path):
        if f.endswith(".csv") or f.endswith(".CSV"):
            with open(os.path.join(metadata_path, f), 'rt') as csvfile:
                csv_reader = csv.reader(csvfile)

                experiment_details = []
                for row in csv_reader:
                    if row[0] == PROJECT:
                        if len(row[1]) > 0:
                            descr = row[1]
                            if project == "N/A":
                                project = descr
                            elif project != descr:
                                print("Project Mismatch: Please ensure all project fields within one experiment share the same value", f)
                                return False
                        else:
                            print("Field Missing: project in " + str(os.path.join(metadata_path, f)))
                    if row[0] == OWNER:
                        if len(row[1]) > 0:
                            descr = row[1]
                            if creator == "N/A":
                                creator = descr
                            elif creator != descr:
                                print("Creator Mismatch: Please ensure all creator fields within one experiment share the same value", f)
                                return False
                    elif row[0] == EXPERIMENT_NAME:
                        if len(row[1]) > 0:
                            label = row[1].split(",")
                            label = '-'.join(label)
                            experiment_details.append(label)
                curr_experiment = "-".join(experiment_details)
                curr_experiment = multiple_replace(curr_experiment)
                if experiment == "N/A":
                    experiment = curr_experiment
                elif experiment != curr_experiment:
                    print("Experiment Mismatch: Please ensure all experiment specific parameters share the same values", f)
                    return False

    return creator, experiment, project


def _get_media_substrate_description(metadata_dict):
    media_substrate_description = ''

    media_components_dict = json.loads(metadata_dict[MEDIA_COMPONENTS])

    for media_descriptor in MEDIA_DESCRIPTOR_LIST:
        if media_descriptor in metadata_dict.keys() and metadata_dict[media_descriptor] != '':
            if media_substrate_description != "":
                media_substrate_description += ', '
            if metadata_dict[media_descriptor] != "none":
                media_substrate_description += metadata_dict[media_descriptor]
    for item in media_components_dict.items():
        media_substrate_description = media_substrate_description + ", " + str(item[1])
    return media_substrate_description,media_components_dict


def parse_metadata_post_experiment_upload(metadata_path, ale_experiment_primary_key):
    if not is_valid(metadata_path, "metadata/xpmdvalidator/Json_schema.json"):
        print ("Invalid metadata!", metadata_path)

    for f in os.listdir(metadata_path):
        if f.endswith(".csv") or f.endswith(".CSV"):

            with open(os.path.join(metadata_path, f), 'rt') as csvfile:
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

            if MEDIA_CARBON_SOURCE in metadata_dict.keys():
                carbon_source = metadata_dict[MEDIA_CARBON_SOURCE]


            if LIBRARY_PREP_KIT_CYCLES in metadata_dict.keys():
                if library_prep != "":
                    library_prep += "/ "
                library_prep += metadata_dict[LIBRARY_PREP_KIT_CYCLES]

            media_temperature = DEFAULT_TEMPERATURE
            environmental_conditions_dict = json.loads(metadata_dict[ENVIRONMENTAL_CONDITIONS])
            if MEDIA_TEMPERATURE in environmental_conditions_dict.keys() and environmental_conditions_dict[MEDIA_TEMPERATURE] != "":
                media_temperature = float(environmental_conditions_dict[MEDIA_TEMPERATURE])

            experiment_details = ""
            if EXPERIMENT_DETAILS in metadata_dict.keys():
                experiment_details = metadata_dict[EXPERIMENT_DETAILS]

            media_substrate_description, media_components_dict = _get_media_substrate_description(metadata_dict)

            ale_id = tech_rep.isolate.flask.ale_id
            ale_id.description = ale_id_description
            ale_id.strain = strain
            if ale_id.species is None: ale_id.species = ""
            ale_id.save()

            media, created = Media.objects.get_or_create(description=media_description,
                                                         substrate=media_substrate_description,
                                                         temperature=media_temperature,
                                                         volume=DEFAULT_VOLUME,
                                                         stirring_speed=DEFAULT_STIRRING_SPEED,
                                                         carbon_source=carbon_source)

            for component in MEDIA_DESCRIPTOR_LIST:
                if component in media_components_dict.keys():
                    remove_spaces = component.replace(' ', '_')
                    setattr(media, remove_spaces, media_components_dict[component])


            media.save()

            flask = tech_rep.isolate.flask
            flask.media = media
            flask.save()

            isolate = tech_rep.isolate
            isolate.library_prep = library_prep
            isolate.save()

            tech_rep.description = experiment_details
            tech_rep.save()

            project, created = Project.objects.get_or_create(name=metadata_dict[PROJECT])


