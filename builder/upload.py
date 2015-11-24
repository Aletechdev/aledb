from os.path import join

import re

from bs4 import BeautifulSoup

from seq.alchemy_orm import *

from gdparse.gdparse import gdparse

import util


EXPERIMENT_PARENT_DIR = "breseq/"  # TODO: See if this is necessary.

HTML_SUMMARY_FILE_NAME = "summary.html"
HTML_MUTATION_FILE_NAME = "index.html"

CLONAL_HTML_CLASSES_TO_PARSE_FOR_MUTATIONS = ["normal_table_row"]
POPULATION_HTML_CLASSES_TO_PARSE_FOR_MUTATIONS = ["normal_table_row", "polymorphism_table_row"]

CLONAL_PROTEIN_CHANGE_INDEX = 3
POPULATION_PROTEIN_CHANGE_INDEX = 4

POPULATION_MUTATION_FREQUENCY_INDEX = 3

AVERAGE_READ_LENGTH_INDEX = 5
READ_COUNT_INDEX = 2

OUTPUT_GENOMIC_DIFF_FILE_NAME = 'output.gd'
ANNOTATION_GENOMIC_DIFF_FILE_NAME = 'annotated.gd'
ANNOTATION_GENOMIC_DIFF_FILE_DIR = '/evidence/'


def add_breseq_results(db_session,
                       isolate_id,
                       person,
                       breseq_folder,
                       is_wild_type=False):
    """
    Figures out if the sample is clonal or population,
    and calls the appropriate "add" function.
    Read the output/log.txt file for " -p " option, which indicates that
    sample was processed as a population.
    """

    # breseq_log_file_path = breseq_folder + util.BRESEQ_LOG_FILE

    # sample_type = util.is_sample_clonal_or_population(breseq_log_file_path)

    #TODO: this should return whether sample is population or clonal.
    # experiment_mutation_dict, \
    #     experiment_mutation_annotation_dict, \
    #     experiment_evidence_dict,\
    #     sample_meta_data_dict = _get_genomic_diff_sample_info(breseq_folder)

    with open(join(breseq_folder, OUTPUT_GENOMIC_DIFF_FILE_NAME), 'rb') as output_genomic_diff_file:

        gd_parser = gdparse.GDParser(file_handle=output_genomic_diff_file)

        sample_mutation_dict = gd_parser.data[gdparse.MUTATION_KEY]

        sample_evidence_dict = gd_parser.data[gdparse.EVIDENCE_KEY]

        sample_reseq_type = gd_parser.meta_data[gdparse.RESEQ_TYPE_KEY]

    annotated_output_file_dir = breseq_folder + ANNOTATION_GENOMIC_DIFF_FILE_DIR

    with open(join(annotated_output_file_dir, ANNOTATION_GENOMIC_DIFF_FILE_NAME), 'rb') as annotation_genomic_diff_file:

        gd_parser = gdparse.GDParser(file_handle=annotation_genomic_diff_file)

        sample_mutation_annotation_dict = gd_parser.data[gdparse.MUTATION_KEY]

    seq_experiment = _get_reseq_experiment_with_stats(db_session,
                                                      breseq_folder,
                                                      isolate_id,
                                                      person)
    db_session.add(seq_experiment)

    _process_mutations(sample_reseq_type,
                       breseq_folder,
                       db_session,
                       seq_experiment,
                       sample_mutation_dict,
                       sample_mutation_annotation_dict,
                       is_wild_type)

    _process_unassigned_missing_coverage(db_session,
                                         seq_experiment,
                                         sample_evidence_dict)


def _get_beautifulsoup_html(output_folder, html_file_name):
    output_file_path = join(output_folder, html_file_name)

    with open(output_file_path) as infile:
        bs_html_file = BeautifulSoup(infile)

    return bs_html_file


def _is_missing_coverage_type(evidence_dict):
    is_missing_coverage = False

    if evidence_dict[gdparse.EVIDENCE_TYPE_KEY] \
            == gdparse.MISSING_COVERAGE_EVIDENCE_TYPE:
        is_missing_coverage = True

    return is_missing_coverage


# Should be able to re-use this with populations.
def _process_unassigned_missing_coverage(db_session, seq_experiment, evidence_dict):
    for key in evidence_dict:

        if _is_missing_coverage_type(evidence_dict[key]):
            # TODO: make literals into constants
            # Followed example given by ObservedMutations.
            # Seems like I have to use a mix of both Django and Alchemy ORM members.
            # Shouldn't have to do this.
            missing_coverage = UnassignedMissingCoverageEvidence()
            missing_coverage.seq_id = evidence_dict[key]['seq_id']
            missing_coverage.start = evidence_dict[key]['start']
            missing_coverage.end = evidence_dict[key]['end']
            missing_coverage.experiment = seq_experiment

            db_session.add(missing_coverage)


def _parse_average_read_length(read_row_input):
    output = re.findall("\d+.\d+", read_row_input)[0]

    return output


def _parse_read_count(read_row_input):
    return int(read_row_input.replace(",", ""))


def _get_reseq_experiment_with_stats(db_session, breseq_folder, isolate_id, person):
    seq_experiment = query_or_create(db_session,
                                     ResequencingExperiment,
                                     location=breseq_folder[breseq_folder.find(EXPERIMENT_PARENT_DIR)
                                                            + len(EXPERIMENT_PARENT_DIR):],
                                     isolate_id=isolate_id,
                                     person=person)

    statistics_html = _get_beautifulsoup_html(breseq_folder, HTML_SUMMARY_FILE_NAME)

    row_read_info = statistics_html.find("tr", attrs={"class": "highlight_table_row"}).findChildren("td")

    # if any mutations were read in, we need to overwrite them
    # ??? WHY ??? -Patrick
    seq_experiment.mutations = []
    seq_experiment.reads = _parse_read_count(row_read_info[READ_COUNT_INDEX].text)
    seq_experiment.average_read_length = _parse_average_read_length(row_read_info[AVERAGE_READ_LENGTH_INDEX].text)

    try:
        seq_experiment.percentage_mapped = float(row_read_info[7].text.replace("%", ""))
    except:
        None

    # average coverage is 3rd table, 2nd row (could also be more rows), 5th column
    mean_coverage = statistics_html.findChildren("table")[2].findChildren("tr")[1].findChildren("td")[4].text
    try:
        mean_coverage = float(mean_coverage)
    except:
        mean_coverage = 0

    seq_experiment.mean_coverage = mean_coverage

    return seq_experiment


# def _get_genomic_diff_sample_info(output_file_dir):
#
#     with open(join(output_file_dir, OUTPUT_GENOMIC_DIFF_FILE_NAME), 'rb') as output_genomic_diff_file:
#
#         gd_parser = gdparse.GDParser(file_handle=output_genomic_diff_file)
#
#         sample_mutation_dict = gd_parser.data[gdparse.MUTATION_KEY]
#
#         sample_evidence_dict = gd_parser.data[gdparse.EVIDENCE_KEY]
#
#         sample_meta_data_dict = gd_parser.meta_data
#
#     annotated_output_file_dir = output_file_dir + ANNOTATION_GENOMIC_DIFF_FILE_DIR
#
#     with open(join(annotated_output_file_dir, ANNOTATION_GENOMIC_DIFF_FILE_NAME), 'rb') as annotation_genomic_diff_file:
#
#         gd_parser = gdparse.GDParser(file_handle=annotation_genomic_diff_file)
#
#         sample_mutation_annotation_dict = gd_parser.data[gdparse.MUTATION_KEY]
#
#     return sample_mutation_dict, sample_mutation_annotation_dict, sample_evidence_dict, sample_meta_data_dict


GD_MUT_POS_ATTR_KEY = 'position'
GD_MUT_GENE_NAME_ATTR_KEY = 'gene_name'
GD_MUT_TYPE_ATTR_KEY = 'type'
GD_MUT_FREQ_ATTR_KEY = 'frequency'

CLONAL_ASSUMED_FREQ = 1


def _process_mutations(sample_type,
                       breseq_folder,
                       db_session,
                       seq_experiment,
                       experiment_mutation_dict,
                       experiment_mutation_annotation_dict,
                       is_wild_type):

    mutations_html = _get_beautifulsoup_html(breseq_folder, HTML_MUTATION_FILE_NAME)

    mutation_rows = _get_mutations_rows(mutations_html, sample_type)

    for row_num, row in enumerate(mutation_rows):

        mutation_num = row_num + 1  # row_num is 0 based, mutation_num is 1 based.

        attrs = row.findChildren("td")
        mutation = query_or_create(db_session,
                                   Mutation,
                                   position=experiment_mutation_dict[mutation_num][GD_MUT_POS_ATTR_KEY],
                                   gene=experiment_mutation_annotation_dict[mutation_num][GD_MUT_GENE_NAME_ATTR_KEY],
                                   # mutations are in the same order in the html and output.gd
                                   # files so we can index the ids with row_num
                                   sequence_change=attrs[2].text,
                                   mutation_type=experiment_mutation_dict[mutation_num][GD_MUT_TYPE_ATTR_KEY])

        '''
        TODO: find out why this is used. I'm avoiding using it for now, since the mutation table won't the mutations
        for those samples which have this set to true.
        '''
        if is_wild_type:
            mutation.reference_error = True

        if mutation.protein_change is None:

            if sample_type == gdparse.SampleType.CLONAL:

                protein_change_index = CLONAL_PROTEIN_CHANGE_INDEX

            else:

                protein_change_index = POPULATION_PROTEIN_CHANGE_INDEX

            change = attrs[protein_change_index].renderContents()
            mutation.protein_change = change

        observed_mutation = ObservedMutation()
        observed_mutation.experiment = seq_experiment
        observed_mutation.mutation = mutation
        observed_mutation.breseq_present = True
        observed_mutation.evidence = attrs[0].renderContents()
        observed_mutation.frequency = _get_mutation_freq(experiment_mutation_dict[mutation_num])

        db_session.add(observed_mutation)


def _get_mutation_freq(mutation_dict):

    frequency = CLONAL_ASSUMED_FREQ

    if GD_MUT_FREQ_ATTR_KEY in mutation_dict:
        frequency = mutation_dict[GD_MUT_FREQ_ATTR_KEY]

    return frequency


def _get_mutations_rows(mutations_html, sample_type):

    # parse the mutation html file to find the correct table

    if sample_type == gdparse.SampleType.CLONAL:

        html_class_to_parse = CLONAL_HTML_CLASSES_TO_PARSE_FOR_MUTATIONS

    else:

        html_class_to_parse = POPULATION_HTML_CLASSES_TO_PARSE_FOR_MUTATIONS

    mutation_table = mutations_html.find("th",
                                         attrs={"class": "mutation_header_row"}).parent.parent

    mutation_rows = mutation_table.findChildren("tr", attrs={"class": html_class_to_parse})

    return mutation_rows
