import datetime

import os

import seq.alchemy_orm

import ale.models

import seq.models

import builder.util

import builder.upload

import builder.key_mutations

from gdparse.gdparse import gdparse


WILD_TYPE_ALE_NUMBER = 0

WILD_TYPE_FLASK_NUMBER = 0

WILD_TYPE_ISOLATE_NUMBER = 1

WILD_TYPE_USER_NAME = "BOP27"

BRESEQ_OUTPUT_REPORT_DIR = "output/"

BRESEQ_OUTPUT_REPORT_FILE = "index.html"

BRESEQ_LOG_FILE = "log.txt"

OUTPUT_GENOMIC_DIFF_FILE_NAME = 'output.gd'

ANNOTATION_GENOMIC_DIFF_FILE_NAME = 'annotated.gd'

ANNOTATION_GENOMIC_DIFF_FILE_DIR = '/evidence/'

# TODO: Don't use defaults any longer.

DEFAULT_INSTRUMENT_NAME = "UCSD1"

DEFAULT_DATE = datetime.date(2013, 1, 1)

DEFAULT_IS_SIMULATION = False

DEFAULT_MEDIA_DESCRIPTION = "M9"

DEFAULT_MEDIA_SUBSTRATE = "glucose"

DEFAULT_TEMPERATURE = 37

DEFAULT_VOLUME = 15

DEFAULT_STIRRING_SPEED = 1100

DEFAULT_FREEZER_BOX_NAME = "ALE box"

DEFAULT_FREEZER_BOX_NUMBER = 1


def remove_flask(flask_primary_key):

    flask_to_delete = ale.models.Flask.objects.get(pk=flask_primary_key)

    flask_to_delete.delete()

    _delete_all_orphaned_mutations()


def delete_ale_experiment(ale_experiment_primary_key):

    """
    Executed from Django ipython shell.
    """

    ale_experiment_to_delete = ale.models.AleExperiment.objects.get(pk=ale_experiment_primary_key)

    ale_experiment_to_delete.delete()

    _delete_all_orphaned_mutations()


def _delete_all_orphaned_mutations():

    all_mutations = seq.models.Mutation.objects.all()

    for mutation in all_mutations:

        if len(mutation.observedmutation_set.all()) == 0:

            mutation.delete()


# TODO: separate adding wild type into another function.
def create_ale_experiment_or_insert_flasks(breseq_output_abs_path,
                                           ale_exp_user,
                                           ale_exp_name,
                                           breseq_wild_type_output_abs_path=None):

    """
    Executed from Django ipython shell.
    """

    sanitized_breseq_output_abs_path = builder.util.sanitize_path(breseq_output_abs_path)

    db_session = seq.alchemy_orm.Session()

    instrument_orm = seq.alchemy_orm.query_or_create(db_session,
                                                     seq.alchemy_orm.Instrument,
                                                     name=DEFAULT_INSTRUMENT_NAME)

    experiment_orm = seq.alchemy_orm.query_or_create(db_session,
                                                     seq.alchemy_orm.AleExperiment,
                                                     name=ale_exp_name,
                                                     instrument=instrument_orm,
                                                     person=ale_exp_user,
                                                     date=DEFAULT_DATE,
                                                     simulation=DEFAULT_IS_SIMULATION)

    media_orm = seq.alchemy_orm.query_or_create(db_session,
                                                seq.alchemy_orm.Media,
                                                description=DEFAULT_MEDIA_DESCRIPTION,
                                                substrate=DEFAULT_MEDIA_SUBSTRATE,
                                                temperature=DEFAULT_TEMPERATURE,
                                                volume=DEFAULT_VOLUME,
                                                stirring_speed=DEFAULT_STIRRING_SPEED)

    freezer_box_orm = seq.alchemy_orm.query_or_create(db_session,
                                                      seq.alchemy_orm.FreezerBox,
                                                      name=DEFAULT_FREEZER_BOX_NAME,
                                                      number=DEFAULT_FREEZER_BOX_NUMBER)

    if breseq_wild_type_output_abs_path is not None:

        sanitized_breseq_output_wild_type_abs_path = builder.util.sanitize_path(breseq_wild_type_output_abs_path)

        _create_and_commit_wild_type_ale_entry(db_session,
                                               sanitized_breseq_output_wild_type_abs_path,
                                               experiment_orm,
                                               media_orm,
                                               freezer_box_orm)

    # Might need to explicitly sort this list in the future.
    breseq_sample_report_list = _get_sample_report_list(sanitized_breseq_output_abs_path)

    for ale_isolate_name in breseq_sample_report_list:

        ale_number = builder.util.parse_ale_name(ale_isolate_name, builder.util.AleName.Ale)

        flask_number = builder.util.parse_ale_name(ale_isolate_name, builder.util.AleName.Flask)

        isolate_number = builder.util.parse_ale_name(ale_isolate_name, builder.util.AleName.Isolate)

        output_path = sanitized_breseq_output_abs_path \
                      + ale_isolate_name \
                      + "/" \
                      + BRESEQ_OUTPUT_REPORT_DIR

        _create_and_commit_ale_entry(db_session,
                                     ale_exp_user,
                                     output_path,
                                     ale_number,
                                     flask_number,
                                     isolate_number,
                                     experiment_orm,
                                     media_orm,
                                     freezer_box_orm,
                                     is_wild_type=False)

    rebuild_key_mutations(experiment_orm.ale_id)


def rebuild_key_mutations(ale_experiment_id):

    _delete_key_mutations(ale_experiment_id)

    _create_key_mutations(ale_experiment_id)


def _delete_key_mutations(ale_experiment_id):

    ale.models.KeyMutation.objects.filter(ale_experiment=ale_experiment_id).delete()


def _create_key_mutations(ale_experiment_id):

    """
    Find all key mutations for ALE experiment and populate database table with them.
    Using only Django ORM to make commit to database.
    """

    django_orm_ale_exp = ale.models.AleExperiment.objects.get(ale_id=ale_experiment_id)

    key_mutations_list = builder.key_mutations.get_key_mutation_list_single_experiment(ale_experiment_id)

    for key_mutation in key_mutations_list:
        django_orm_key_mutation = ale.models.KeyMutation()
        django_orm_key_mutation.ale_experiment = django_orm_ale_exp
        django_orm_key_mutation.mutation = key_mutation
        django_orm_key_mutation.save()


def _create_and_commit_wild_type_ale_entry(db_session,
                                           breseq_wild_type_abs_path,
                                           experiment,
                                           media,
                                           freezer_box):

    # Setting the "is_wild_type" flag to true hides the mutation information.
    # This was implemented because originally, the implementers didn't want to
    # view the wild type mutations along with the actual mutations.
    # This is not the case for us, where we want to see the wild type mutations
    # along with the sample mutations since we're using the wild type mutations
    # for filtering with key mutations.

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
                                 is_wild_type=False)


def _create_and_commit_ale_entry(db_session,
                                 person,
                                 breseq_folder_path,
                                 ale_number,
                                 flask_number,
                                 isolate_number,
                                 experiment,
                                 media,
                                 freezer_box,
                                 is_wild_type):

    """
    is_wild_type was implemented because initially, we wanted to ignore
    mutations that were already thought to be in the wild type strain,
    yet not included in the reference. For instance,
    if a mutation existed in BW25311, which is a derivative of MG1655,
    though we have to use the reference for MG1655 in resequencing,
    we can set particular mutations to is_wild_type = true,
    which won't show the mutation in the tables.

    The case for wild type mutations is that now we want to keep them
    in the mutation tables because they serve as QC mechanisms for
    seeing which starting strain mutations have persisted and which
    have changed.
    """

    ale_id = seq.alchemy_orm.query_or_create(db_session,
                                             seq.alchemy_orm.AleId,
                                             ale_experiment=experiment,
                                             ale_id=ale_number)

    flask = seq.alchemy_orm.query_or_create(db_session,
                                            seq.alchemy_orm.Flask,
                                            flask_number=flask_number,
                                            ale_id=ale_id,
                                            media=media)

    with open(os.path.join(breseq_folder_path, OUTPUT_GENOMIC_DIFF_FILE_NAME), 'rb') as output_genomic_diff_file:

        mutation_gd_parser = gdparse.GDParser(file_handle=output_genomic_diff_file)

    annotated_output_file_dir = breseq_folder_path + ANNOTATION_GENOMIC_DIFF_FILE_DIR

    with open(os.path.join(annotated_output_file_dir, ANNOTATION_GENOMIC_DIFF_FILE_NAME), 'rb') as annotation_genomic_diff_file:

        annotation_gd_parser = gdparse.GDParser(file_handle=annotation_genomic_diff_file)

    reseq_reference = mutation_gd_parser.meta_data[gdparse.GENOMIC_DIFF_SEQ_REF_KEY]

    reseq_date = ""
    if gdparse.GENOMIC_DIFF_CREATED_KEY in mutation_gd_parser.meta_data.keys():
        reseq_date = mutation_gd_parser.meta_data[gdparse.GENOMIC_DIFF_CREATED_KEY]

    breseq_version = ""
    if gdparse.BRESEQ_VERSION_KEY in mutation_gd_parser.meta_data.keys():
        breseq_version = mutation_gd_parser.meta_data[gdparse.BRESEQ_VERSION_KEY]

    if gdparse.RESEQ_TYPE_KEY in mutation_gd_parser.meta_data.keys():

        sample_reseq_type = mutation_gd_parser.meta_data[gdparse.RESEQ_TYPE_KEY]

    else:  # Breseq version 0.26.0 doesn't have the #=COMMAND meta-data.

        sample_reseq_type = _legacy_get_sample_reseq_type(breseq_folder_path)

        mutation_gd_parser.meta_data[gdparse.RESEQ_TYPE_KEY] = sample_reseq_type

    is_population = False

    if sample_reseq_type == gdparse.SampleType.POPULATION:

        is_population = True

    isolate = seq.alchemy_orm.query_or_create(db_session,
                                              seq.alchemy_orm.Isolate,
                                              flask=flask,
                                              isolate_number=isolate_number,
                                              is_population=is_population,
                                              reseq_reference=reseq_reference,
                                              reseq_date=reseq_date,
                                              breseq_version=breseq_version,
                                              freezer_box=freezer_box,
                                              person=person)

    db_session.commit()

    builder.upload.add_breseq_results(db_session=db_session,
                                      isolate_id=isolate.id,
                                      person=person,
                                      breseq_folder=breseq_folder_path,
                                      mutation_gd_parser=mutation_gd_parser,
                                      annotation_gd_parser=annotation_gd_parser,
                                      is_wild_type=is_wild_type)

    db_session.commit()


def _legacy_get_sample_reseq_type(breseq_folder_path):

    sample_reseq_type = gdparse.SampleType.CLONAL

    breseq_log_file_path = breseq_folder_path + BRESEQ_LOG_FILE

    if gdparse.BRESEQ_POPULATION_OPTION in open(breseq_log_file_path).read():

        sample_reseq_type = gdparse.SampleType.POPULATION

    return sample_reseq_type


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
