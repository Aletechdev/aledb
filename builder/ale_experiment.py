import os
import ale.models
import builder.upload
import builder.util
from fixation.models import FixatedMutation
import fixation.util
import converge.util
from converge.models import ConvergeMutation
import seq.models
import seq.views.common
from builder.gdparse.gdparse import gdparse
from common.util import clear_dashboard_cache
import metadata.parser
from dashboard.timeline_util import create_event
from dashboard.util import rebuild_dashboard_data
from filter.models import AleExperimentFilter
import filter.models


WILD_TYPE_ALE_NUMBER = 0
WILD_TYPE_FLASK_NUMBER = 0
WILD_TYPE_ISOLATE_NUMBER = 1
WILD_TYPE_TECH_REP_NUMBER = 1
WILD_TYPE_USER_NAME = "BOP27"
BRESEQ_OUTPUT_REPORT_DIR = "output/"
BRESEQ_LOG_FILE = "log.txt"
ANNOTATION_GENOMIC_DIFF_FILE_NAME = 'annotated.gd'
METADATA_RELATIVE_PATH = 'metadata/'
REF_RELATIVE_PATH = 'ref/'


def integrate_metadata(ale_exp_path, ref_file_name, ale_exp_primary_key):
    """
    Executed from Django ipython shell
    """
    metadata_path = ale_exp_path + METADATA_RELATIVE_PATH
    metadata.parser.parse_metadata_post_experiment_upload(metadata_path, ale_exp_primary_key)

    ref_file_path = ale_exp_path + REF_RELATIVE_PATH + ref_file_name
    create_functional_annotations(ref_file_path, ale_exp_primary_key)


def remove_flask(flask_primary_key):
    """
    Executed from Django ipython shell
    """
    clear_dashboard_cache()
    flask_to_delete = ale.models.Flask.objects.get(pk=flask_primary_key)
    flask_to_delete.delete()
    _delete_all_orphaned_mutations()


def delete_ale_experiments(ale_experiment_primary_key_list):
    """
    Executed from Django ipython shell.
    """
    for exp_id in ale_experiment_primary_key_list:
        ale_experiment_to_delete = ale.models.AleExperiment.objects.get(pk=exp_id)
        message = "Experiment %s was deleted" % ale_experiment_to_delete.name
        ale_experiment_to_delete.delete()
        _delete_all_orphaned_mutations()
        rebuild_dashboard_data()
        create_event(title="Experiment Deleted",
                    message=message,
                    icon='<i class="fa fa-times" aria-hidden="true"></i>',
                    color="danger")


def _delete_all_orphaned_mutations():
    all_mutations = seq.models.Mutation.objects.all()
    for mutation in all_mutations:
        if len(mutation.observedmutation_set.all()) == 0:
            mutation.delete()


def delete_isolate(ale_experiment_primary_key, ale_number, flask_number, isolate_number):
    isolate_to_delete = ale.models.Isolate.objects.filter(isolate_number=isolate_number)
    for isolate in isolate_to_delete:
        if isolate.flask.ale_id.ale_experiment_id == ale_experiment_primary_key and isolate.flask.ale_id.ale_id == ale_number and isolate.flask.flask_number == flask_number:
            isolate.delete()
            print("Successfully removed: ", ale_number, flask_number, isolate_number)
    _delete_all_orphaned_mutations()


def insert_starting_strain_flask(starting_strain_breseq_output_abs_path, ale_exp_user, ale_exp_name):
    """
    Executed from Django ipython shell.
    Args:
        starting_strain_breseq_output_abs_path (list): A string list of the absolution path of the output directory of a breseq report.
        ale_exp_user (string): A string for the user name associated with the target ALE experiment.
        ale_exp_name (string): A string for the target ALE experiment name.
    """

    clear_dashboard_cache()

    instrument_orm = ale.models.Instrument.objects.get_or_create(name=metadata.parser.DEFAULT_INSTRUMENT_NAME)

    experiment_orm = ale.models.AleExperiment.objects.get_or_create(name=ale_exp_name,
                                                                    instrument=instrument_orm,
                                                                    person=ale_exp_user)

    media_orm = ale.models.Media.objects.get_or_create(description=metadata.parser.DEFAULT_MEDIA_DESCRIPTION,
                                                       substrate=metadata.parser.DEFAULT_MEDIA_SUBSTRATE,
                                                       temperature=metadata.parser.DEFAULT_TEMPERATURE,
                                                       volume=metadata.parser.DEFAULT_VOLUME,
                                                       stirring_speed=metadata.parser.DEFAULT_STIRRING_SPEED)

    freezer_box_orm = ale.models.FreezerBox.objects.get_or_create(name=metadata.parser.DEFAULT_FREEZER_BOX_NAME,
                                                                  number=metadata.parser.DEFAULT_FREEZER_BOX_NUMBER)

    _insert_starting_strain_flask(starting_strain_breseq_output_abs_path,
                                  ale_exp_user,
                                  ale_exp_name,
                                  experiment_orm,
                                  media_orm,
                                  freezer_box_orm)

    rebuild_converge_mutations(experiment_orm.ale_id)
    rebuild_fixated_mutations(experiment_orm.ale_id)
    rebuild_dashboard_data()


def rebuild_all_fixated_mutations():
    ale_experiment_queryset = ale.models.AleExperiment.objects.all()
    for ale_experiment in ale_experiment_queryset:
        rebuild_fixated_mutations(ale_experiment.ale_id)


def rebuild_all_converged_mutations():
    ale_experiment_queryset = ale.models.AleExperiment.objects.all()
    for ale_experiment in ale_experiment_queryset:
        rebuild_converge_mutations(ale_experiment.ale_id)


def _insert_starting_strain_flask(staring_strain_breseq_output_abs_path,
                                  ale_exp_user,
                                  ale_exp_name,
                                  experiment_orm,
                                  media_orm,
                                  freezer_box_orm):

    sanitized_breseq_output_wild_type_abs_path = builder.util.sanitize_path(staring_strain_breseq_output_abs_path)

    _create_and_commit_wild_type_ale_entry(sanitized_breseq_output_wild_type_abs_path,
                                           experiment_orm,
                                           media_orm,
                                           freezer_box_orm)


def create_ale_experiments(exp_files_dict_list):
    """
    Executed from Django ipython shell.
    """ 
    for exp_files_dict in exp_files_dict_list:
        create_ale_experiment(exp_files_dict["breseq_output_group_root_abs_path"],
                              exp_files_dict["ale_exp_user"],
                              exp_files_dict["ale_exp_name"],
                              exp_files_dict["breseq_starting_strain_output_abs_path"]) 


# For wild_type, expecting directory with output.gd in it.
def create_ale_experiment(breseq_output_group_root_abs_path,
                          ale_exp_user,
                          ale_exp_name,
                          breseq_starting_strain_output_abs_path=None):

    """
    Executed from Django ipython shell.
    """

    clear_dashboard_cache() #TODO: remove, since no longer using cache.

    breseq_output_group_root_abs_path = builder.util.sanitize_path(breseq_output_group_root_abs_path)

    instrument, created = ale.models.Instrument.objects.get_or_create(name=metadata.parser.DEFAULT_INSTRUMENT_NAME)
    experiment, created = ale.models.AleExperiment.objects.get_or_create(name=ale_exp_name,
                                                                         instrument=instrument,
                                                                         person=ale_exp_user)

    create_event(title="Experiment Created",
                 message="Experiment %s was created" % experiment.name,
                 icon='<i class="fa fa-flask" aria-hidden="true"></i>',
                 color="success")

    default_media, \
    created = ale.models.Media.objects.get_or_create(description=metadata.parser.DEFAULT_MEDIA_DESCRIPTION,
                                                                    substrate=metadata.parser.DEFAULT_MEDIA_SUBSTRATE,
                                                                    temperature=metadata.parser.DEFAULT_TEMPERATURE,
                                                                    volume=metadata.parser.DEFAULT_VOLUME,
                                                                    stirring_speed=metadata.parser.DEFAULT_STIRRING_SPEED)

    freezer_box, created = ale.models.FreezerBox.objects.get_or_create(name=metadata.parser.DEFAULT_FREEZER_BOX_NAME,
                                                                       number=metadata.parser.DEFAULT_FREEZER_BOX_NUMBER)

    if breseq_starting_strain_output_abs_path is not None:
        _insert_starting_strain_flask(breseq_starting_strain_output_abs_path,
                                      ale_exp_user,
                                      ale_exp_name,
                                      experiment,
                                      default_media,
                                      freezer_box)

    # Might need to explicitly sort this list in the future.
    breseq_sample_report_list = _get_sample_report_list(breseq_output_group_root_abs_path)
    for ale_isolate_name in breseq_sample_report_list:
        ale_number = builder.util.parse_ale_name(ale_isolate_name, builder.util.AleName.Ale)
        flask_number = builder.util.parse_ale_name(ale_isolate_name, builder.util.AleName.Flask)
        isolate_number = builder.util.parse_ale_name(ale_isolate_name, builder.util.AleName.Isolate)
        technical_replicate_number = builder.util.parse_ale_name(ale_isolate_name, builder.util.AleName.TechnicalReplicate)
        print(ale_number, flask_number, isolate_number, technical_replicate_number)
        output_path = breseq_output_group_root_abs_path + ale_isolate_name + "/" + BRESEQ_OUTPUT_REPORT_DIR
        _create_and_commit_ale_entry(ale_exp_user,
                                     output_path,
                                     ale_number,
                                     flask_number,
                                     isolate_number,
                                     technical_replicate_number,
                                     experiment,
                                     default_media,
                                     freezer_box,
                                     is_wild_type=False)

    default_filter_params = filter.models.get_default_experiment_filter_params(experiment)
    AleExperimentFilter.objects.get_or_create(**default_filter_params)
    rebuild_converge_mutations(experiment.ale_id)
    rebuild_fixated_mutations(experiment.ale_id)
    rebuild_dashboard_data()


def rebuild_fixated_mutations(ale_experiment_id):
    _delete_fixated_mutations(ale_experiment_id)
    _create_fixated_mutations(ale_experiment_id)


def _delete_fixated_mutations(ale_experiment_id):
    FixatedMutation.objects.filter(ale_experiment=ale_experiment_id).delete()


def _create_fixated_mutations(ale_experiment_id):
    """
    Find all fixated mutations for an ALE experiment and populate database table with them.
    Using only Django ORM to make commit to database.
    """
    ale_experiment = ale.models.AleExperiment.objects.get(ale_id=ale_experiment_id)
    fixed_mut_dict = fixation.util.get_fixed_mut_dict(ale_experiment_id)
    for fixed_mut, fixed_obs_mut_series_list in fixed_mut_dict.items():
        FixatedMutation.objects.create(ale_experiment=ale_experiment, mutation=fixed_mut, fixed_observed_mutation_series=str(fixed_obs_mut_series_list))


def rebuild_converge_mutations(ale_experiment_id):
    _delete_converge_mutations(ale_experiment_id)
    _create_converge_mutations(ale_experiment_id)


def _delete_converge_mutations(ale_experiment_id):
    ConvergeMutation.objects.filter(ale_experiment=ale_experiment_id).delete()


def _create_converge_mutations(ale_experiment_id):
    ale_experiment = ale.models.AleExperiment.objects.get(ale_id=ale_experiment_id)
    converge_mut_list = converge.util.get_converge_mutation_list(ale_experiment_id)
    for mut in converge_mut_list :
        ConvergeMutation.objects.create(ale_experiment=ale_experiment, mutation=mut)


def _create_and_commit_wild_type_ale_entry(breseq_wild_type_abs_path,
                                           experiment,
                                           media,
                                           freezer_box):

    # Setting the "is_wild_type" flag to true hides the mutation information.
    # This was implemented because originally, the implementers didn't want to
    # view the wild type mutations along with the actual mutations.
    # This is not the case for us, where we want to see the wild type mutations
    # along with the sample mutations since we're using the wild type mutations
    # for filtering with key mutations.

    _create_and_commit_ale_entry(WILD_TYPE_USER_NAME,
                                 breseq_wild_type_abs_path,
                                 WILD_TYPE_ALE_NUMBER,
                                 WILD_TYPE_FLASK_NUMBER,
                                 WILD_TYPE_ISOLATE_NUMBER,
                                 WILD_TYPE_TECH_REP_NUMBER,
                                 experiment,
                                 media,
                                 freezer_box,
                                 is_wild_type=True)


def _create_and_commit_ale_entry(person,
                                 breseq_output_dir_path,
                                 ale_number,
                                 flask_number,
                                 isolate_number,
                                 technical_replicate_number,
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

    ale_id, created = ale.models.AleId.objects.get_or_create(ale_experiment=experiment, ale_id=ale_number)
    flask, created = ale.models.Flask.objects.get_or_create(flask_number=flask_number, ale_id=ale_id, media=media)

    with open(os.path.join(breseq_output_dir_path, ANNOTATION_GENOMIC_DIFF_FILE_NAME), 'rb') as annotation_genomic_diff_file:
        mutation_gd_parser = gdparse.GDParser(file_handle=annotation_genomic_diff_file)

    reseq_ref_name = ""
    if gdparse.GENOME_DIFF_SEQ_REF_KEY in mutation_gd_parser.meta_data.keys():
        reseq_ref_name = mutation_gd_parser.meta_data[gdparse.GENOME_DIFF_SEQ_REF_KEY]

    reseq_date = ""
    if gdparse.GENOME_DIFF_CREATED_KEY in mutation_gd_parser.meta_data.keys():
        reseq_date = mutation_gd_parser.meta_data[gdparse.GENOME_DIFF_CREATED_KEY]

    breseq_version = ""
    if gdparse.BRESEQ_VERSION_KEY in mutation_gd_parser.meta_data.keys():
        breseq_version = mutation_gd_parser.meta_data[gdparse.BRESEQ_VERSION_KEY]

    if gdparse.RESEQ_TYPE_KEY in mutation_gd_parser.meta_data.keys():
        sample_reseq_type = mutation_gd_parser.meta_data[gdparse.RESEQ_TYPE_KEY]
    else:  # Breseq version 0.26.0 doesn't have the #=COMMAND meta-data.
        sample_reseq_type = _get_reseq_type(breseq_output_dir_path)
        mutation_gd_parser.meta_data[gdparse.RESEQ_TYPE_KEY] = sample_reseq_type

    is_population = False
    if sample_reseq_type == gdparse.SampleType.POPULATION:
        is_population = True

    isolate, created = ale.models.Isolate.objects.get_or_create(flask=flask,
                                                                isolate_number=isolate_number,
                                                                is_population=is_population,
                                                                reseq_reference=reseq_ref_name,
                                                                reseq_date=reseq_date,
                                                                breseq_version=breseq_version,
                                                                freezer_box=freezer_box,
                                                                person=person)

    technical_replicate, \
    created = ale.models.TechnicalReplicate.objects.get_or_create(tech_rep_number=technical_replicate_number,
                                                                                       isolate=isolate)

    builder.upload.add_breseq_results(technical_replicate_id=technical_replicate.id,
                                      person=person,
                                      breseq_ouput_dir_path=breseq_output_dir_path,
                                      mutation_gd_parser=mutation_gd_parser,
                                      reseq_ref_name=reseq_ref_name,
                                      experiment=experiment,
                                      is_wild_type=is_wild_type, )


def _get_reseq_type(breseq_folder_path):
    sample_reseq_type = gdparse.SampleType.CLONAL
    breseq_log_file_path = breseq_folder_path + BRESEQ_LOG_FILE
    if os.path.isfile(breseq_log_file_path) \
            and gdparse.BRESEQ_POPULATION_EXEC_FLAG in open(breseq_log_file_path).read():
        sample_reseq_type = gdparse.SampleType.POPULATION
    return sample_reseq_type


def _get_sample_report_list(experiment_breseq_output_path):

    breseq_sample_report_list = []

    for breseq_sample_names in os.listdir(experiment_breseq_output_path):

        sample_path = experiment_breseq_output_path + breseq_sample_names
        sample_breseq_output_report = sample_path\
                                      + '/'\
                                      + BRESEQ_OUTPUT_REPORT_DIR \
                                      + ANNOTATION_GENOMIC_DIFF_FILE_NAME

        if os.path.isdir(sample_path) and os.path.isfile(sample_breseq_output_report):
            breseq_sample_report_list.append(breseq_sample_names)

    return breseq_sample_report_list


def create_functional_annotations(genbank_path, ale_experiment_id):

    gene_dict = _parse_genbank(genbank_path)

    observed_mutations = seq.models.ObservedMutation.objects.filter(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment=ale_experiment_id)

    for observed_mutation in observed_mutations:

        mutation = observed_mutation.mutation
        mutation_genes= ""
        if mutation.gene is not None:
            mutation_genes = mutation.gene.replace("[", "").replace("]", "").replace(u"\u2013", "/").replace("-", "/").split("/")

        gene_info_start = {"product": "", "function": "", "go_process": "", "go_component": ""}

        gene_info = gene_info_start

        for gene in mutation_genes:

            gene_info = gene_info_start

            try:
                gene_info['function'] += "(" + gene_dict[gene]['function'] + ")"

                gene_info['product'] += "(" + gene_dict[gene]['product'] + ")"

                gene_info['go_component'] += "(" + gene_dict[gene]['go_component'] + ")"

                gene_info['go_process'] += "(" + gene_dict[gene]['go_process'] + ")"

            except Exception as e:
                # print(e, " Does not exits in ", os.path.basename(genbank_path))
                pass

        mutation.function = gene_info['function']

        mutation.product = gene_info['product']

        mutation.go_component = gene_info['go_component']

        mutation.go_process = gene_info['go_process']

        mutation.save()

    return


def _parse_genbank(genbank_path):

    gene_info_start = {"product": "", "function": "", "go_process": "", "go_component": ""}

    gene_dict = {}

    current_gene = ""

    with open(genbank_path, "rt") as genbank:

        record = False

        gene_info = gene_info_start

        for line in genbank:

            line = line.strip()

            if line.startswith("CDS ") or line.startswith("tRNA ") or line.startswith("rRNA"):

                record = True

            elif line.startswith("gene ") and current_gene is not "":

                gene_dict[current_gene] = dict(gene_info)

                record = False

                gene_info = gene_info_start

            elif line.startswith("ORIGIN"):

                if record is True:

                    gene_dict[current_gene] = gene_info

                break

            else:

                if record is not False:

                    if line.startswith("/gene="):

                        current_gene = _find_between(line, "\"", "\"")

                    elif line.startswith("/product="):

                        gene_info['product'] = _find_between(line, "\"", "\"")

                    elif line.startswith("/function="):

                        gene_info['function'] = _find_between(line, "\"", "\"")

                    elif line.startswith("/GO_process="):

                        gene_info['go_process'] = _find_between(line, "\"", "\"")

                    elif line.startswith("/GO_component="):

                        gene_info['go_component'] = _find_between(line, "\"", "\"")

    return gene_dict


def _find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""
