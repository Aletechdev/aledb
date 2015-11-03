import datetime

import os

import seq.alchemy_orm

import builder.upload

import builder.key_mutations

from builder import util

# import builder.validatemutations  # TODO: find out what validatemutations does for mutations.

from ale.models import AleExperiment

from seq.models import Mutation

from ale.models import KeyMutation

from ale.models import Flask


WILD_TYPE_ALE_NUMBER = 0
WILD_TYPE_FLASK_NUMBER = 0
WILD_TYPE_ISOLATE_NUMBER = 0
WILD_TYPE_USER_NAME = "BOP27"

BRESEQ_OUTPUT_REPORT_DIR = "output/"
BRESEQ_OUTPUT_REPORT_FILE = "index.html"


def remove_flask(flask_primary_key):

    flask_to_delete = Flask.objects.get(pk=flask_primary_key)

    flask_to_delete.delete()

    _delete_all_orphaned_mutations()


def delete_ale_experiment(ale_experiment_primary_key):

    """
    Meant to be executed from Django ipython shell.
    """

    ale_experiment_to_delete = AleExperiment.objects.get(pk=ale_experiment_primary_key)

    ale_experiment_to_delete.delete()

    _delete_all_orphaned_mutations()


def _delete_all_orphaned_mutations():

    all_mutations = Mutation.objects.all()

    for mutation in all_mutations:

        if len(mutation.observedmutation_set.all()) == 0:

            mutation.delete()


# TODO: separate adding wild type into another function.
def create_ale_experiment_or_insert_flasks(breseq_output_abs_path,
                                           ale_exp_user,
                                           ale_exp_name,
                                           breseq_wild_type_output_abs_path=None):

    """
    Meant to be executed from Django ipython shell.
    """

    sanitized_breseq_output_abs_path = util.sanitize_path(breseq_output_abs_path)

    db_session = seq.alchemy_orm.Session()

    # TODO: shouldn't be returning multiple objects, because you remember return order; bad practice.
    experiment,\
    media,\
    freezer_box\
        = _get_project_orm(db_session,
                           ale_exp_user,
                           ale_exp_name)

    if breseq_wild_type_output_abs_path is not None:

        sanitized_breseq_output_wild_type_output_abs_path = util.sanitize_path(breseq_wild_type_output_abs_path)

        _create_and_commit_wild_type_ale_entry(db_session,
                                               sanitized_breseq_output_wild_type_output_abs_path,
                                               experiment,
                                               media,
                                               freezer_box)

    # Might need to explicitly sort this list in the future.
    breseq_sample_report_list = _get_sample_report_list(sanitized_breseq_output_abs_path)

    for ale_isolate_name in breseq_sample_report_list:

        ale_number = util.parse_ale_name(ale_isolate_name, util.AleName.Ale)

        flask_number = util.parse_ale_name(ale_isolate_name, util.AleName.Flask)

        isolate_number = 1  # TODO: find out why is this set to 1 for all endpoints and make it a constant.

        output_path = sanitized_breseq_output_abs_path\
                      + ale_isolate_name\
                      + "/"\
                      + BRESEQ_OUTPUT_REPORT_DIR

        _create_and_commit_ale_entry(db_session,
                                    ale_exp_user,
                                    output_path,
                                    ale_number,
                                    flask_number,
                                    isolate_number,
                                    experiment,
                                    media,
                                    freezer_box,
                                    is_wild_type=False)

    _populate_key_mutations(experiment)


def insert_flask(breseq_output_abs_path,
                 ale_exp_user,
                 ale_exp_name,
                 ale_number,
                 flask_number):

    sanitized_breseq_output_abs_path = util.sanitize_path(breseq_output_abs_path)

    db_session = seq.alchemy_orm.Session()

    # TODO: shouldn't be returning multiple objects, because you remember return order; bad practice.
    experiment,\
    media,\
    freezer_box\
        = _get_project_orm(db_session,
                           ale_exp_user,
                           ale_exp_name)

    breseq_sample_name = util.get_ale_name(ale_number, flask_number)

    output_path = sanitized_breseq_output_abs_path\
                      + breseq_sample_name\
                      + "/"\
                      + BRESEQ_OUTPUT_REPORT_DIR

    isolate_number = 1  # TODO: find out why is this set to 1 for all endpoints and make it a constant.

    _create_and_commit_ale_entry(db_session,
                                 ale_exp_user,
                                 output_path,
                                 ale_number,
                                 flask_number,
                                 isolate_number,
                                 experiment,
                                 media,
                                 freezer_box,
                                 is_wild_type=False)


def _populate_key_mutations(sql_alchemy_experiment):

    """
    Find all key mutations for ALE experiment and populate database table with them.
    Using only Django ORM to make commit to database.
    """

    django_orm_ale_exp = AleExperiment.objects.get(ale_id=sql_alchemy_experiment.ale_id)

    key_mutations_set = builder.key_mutations.get_key_mutations(sql_alchemy_experiment.ale_id)
    key_mutations_list = list(key_mutations_set)

    for key_mutation in key_mutations_list:
        km = KeyMutation()
        km.ale_experiment = django_orm_ale_exp
        km.mutation = key_mutation
        km.save()


def _create_and_commit_wild_type_ale_entry(db_session,
                                           breseq_wild_type_abs_path,
                                           experiment,
                                           media,
                                           freezer_box):

    _create_and_commit_ale_entry(db_session,
                                 WILD_TYPE_USER_NAME,
                                 breseq_wild_type_abs_path,
                                 WILD_TYPE_ALE_NUMBER,
                                 WILD_TYPE_FLASK_NUMBER,
                                 WILD_TYPE_ISOLATE_NUMBER,
                                 experiment,
                                 media,
                                 freezer_box,
                                 # is_wild_type=True
                                 is_wild_type=False)  # This is in fact the wild type, though setting this to false hides the mutations in the mutation table.


def _create_and_commit_ale_entry(db_session,
                                person,
                                breseq_folder,
                                ale_number,
                                flask_number,
                                isolate_number,
                                experiment,
                                media,
                                freezer_box,
                                is_wild_type):

    ale_id = seq.alchemy_orm.query_or_create(db_session,
                                         seq.alchemy_orm.AleId,
                                         ale_experiment=experiment,
                                         ale_id=ale_number)

    flask = seq.alchemy_orm.query_or_create(db_session,
                                        seq.alchemy_orm.Flask,
                                        flask_number=flask_number,
                                        ale_id=ale_id,
                                        media=media)

    isolate = seq.alchemy_orm.query_or_create(db_session,
                                          seq.alchemy_orm.Isolate,
                                          flask=flask,
                                          isolate_number=isolate_number,
                                          is_population=False,
                                          freezer_box=freezer_box,
                                          person=person)

    db_session.commit()

    builder.upload.add_breseq_results(db_session=db_session,
                              isolate_id=isolate.id,
                              person=person,
                              breseq_folder=breseq_folder,
                              is_wild_type=is_wild_type)

    db_session.commit()


# TODO: make all default values used within this script as constants or in a config file.
# TODO: add more parameters to function for inputs set as literals.
def _get_project_orm(db_session,
                     ale_exp_user,
                     ale_exp_name):

    # create the instrument, experiment, etc. to the isolates for the strains
    instrument = seq.alchemy_orm.query_or_create(db_session,
                                                 seq.alchemy_orm.Instrument,
                                                 name="UCSD1")

    experiment = seq.alchemy_orm.query_or_create(db_session,
                                                 seq.alchemy_orm.AleExperiment,
                                                 name=ale_exp_name,
                                                 instrument=instrument,
                                                 person=ale_exp_user,
                                                 date=datetime.date(2013, 1, 1),
                                                 simulation=False)

    media = seq.alchemy_orm.query_or_create(db_session,
                                            seq.alchemy_orm.Media,
                                            description="M9",
                                            substrate="Glycerol",
                                            temperature=30,
                                            volume=15,
                                            stirring_speed=1100)

    freezer_box = seq.alchemy_orm.query_or_create(db_session,
                                                  seq.alchemy_orm.FreezerBox,
                                                  name="ALE box",
                                                  number=1)

    # TODO: find a better way to return these, so that don't have to worry about return order.
    return experiment, media, freezer_box


def _get_sample_report_list(experiment_breseq_output_path):

    breseq_sample_report_list = []

    for breseq_sample_names in os.listdir(experiment_breseq_output_path):

        sample_path = experiment_breseq_output_path + breseq_sample_names
        sample_breseq_output_report = sample_path\
                                      + '/'\
                                      + BRESEQ_OUTPUT_REPORT_DIR\
                                      + BRESEQ_OUTPUT_REPORT_FILE

        if os.path.isdir(sample_path) and os.path.isfile(sample_breseq_output_report):
            breseq_sample_report_list.append(breseq_sample_names)

    return breseq_sample_report_list
