from os.path import join
import re
import sys
import traceback
from bs4 import BeautifulSoup
from builder.gdparse.gdparse import gdparse
import collections
import numbers
from seq.models import Mutation, \
    ObservedMutation, \
    UnassignedMissingCoverageEvidence, \
    ResequencingExperiment
import os
from genes.util import get_annotated_gene_list
from filter.models import AleExperimentFilter
import filter.models
from django.conf import settings

HTML_SUMMARY_FILE_NAME = "summary.html"
HTML_INDEX_FILE_NAME = "index.html"
CLONAL_HTML_CLASSES_TO_PARSE_FOR_MUTATIONS = ["normal_table_row"]
POPULATION_HTML_CLASSES_TO_PARSE_FOR_MUTATIONS = ["normal_table_row", "polymorphism_table_row"]
AVERAGE_READ_LENGTH_INDEX = 5
READ_COUNT_INDEX = 2
GD_MUT_POS_ATTR_KEY = 'position'
GD_MUT_GENE_NAME_ATTR_KEY = 'gene_name'
GD_MUT_GENE_PRODUCT_ATTR_KEY = 'gene_product'  # Will contain list of genes for mutations affecting many.
GD_MUT_TYPE_ATTR_KEY = 'type'
GD_MUT_FREQ_ATTR_KEY = 'frequency'
GATK_MUT_FREQ_ATTR_KEY = ''
GD_MUT_HTML = 'html_mutation'
GD_MUT_ANNOTATION_HTML = "html_mutation_annotation"
GD_MUT_SEQ_ID_ATTR_KEY = 'seq_id'
DEFAULT_CLONAL_FREQ = 1
DEFAULT_GATK_FREQ = 0
BRESEQ_REPORT_COLUMN_KEY_EVIDENCE = "evidence"
BRESEQ_RESULT_RELATIVE_PATH = ""

ale_data_root_dir = settings.ALE_DATA_ROOT_DIR


def add_breseq_results(technical_replicate_id,
                       person,
                       experiment_path,
                       mutation_gd_parser,
                       reseq_ref_name,
                       sample_name,
                       experiment=None,
                       is_wild_type=False):
    """
    Figures out if the sample is clonal or population,
    and calls the appropriate "add" function.
    Read the output/log.txt file for " -p " option, which indicates that
    sample was processed as a population.
    """
    breseq_output_dir_path = '%s/breseq/%s/output/' % (experiment_path, sample_name)
    reseq = _get_reseq_experiment_with_stats(breseq_output_dir_path,
                                             technical_replicate_id,
                                             person)

    sample_reseq_type = gdparse.SampleType.CLONAL  # arbitrary default, though could have side-effects.
    if gdparse.RESEQ_TYPE_KEY in mutation_gd_parser.meta_data.keys():
        sample_reseq_type = mutation_gd_parser.meta_data[gdparse.RESEQ_TYPE_KEY]
    sample_mutation_dict = mutation_gd_parser.data[gdparse.MUTATION_KEY]

    _database_mutations(sample_reseq_type,
                        breseq_output_dir_path,
                        reseq,
                        sample_mutation_dict,
                        experiment,
                        is_wild_type)

    sample_evidence_dict = mutation_gd_parser.data[gdparse.EVIDENCE_KEY]

    _database_unassigned_missing_coverage(reseq,
                                          sample_evidence_dict,
                                          breseq_output_dir_path)


def _get_beautifulsoup_html(output_folder, html_file_name):
    output_file_path = join(output_folder, html_file_name)
    bs_html_file = None
    if os.path.isfile(output_file_path):
        with open(output_file_path) as infile:
            bs_html_file = BeautifulSoup(infile, "html.parser")
    return bs_html_file


def _is_missing_coverage_type(evidence_dict):
    is_missing_coverage = False
    if evidence_dict[gdparse.EVIDENCE_TYPE_KEY] == gdparse.MISSING_COVERAGE_EVIDENCE_TYPE:
        is_missing_coverage = True
    return is_missing_coverage


# Should be able to re-use this with populations.
def _database_unassigned_missing_coverage(seq_experiment, evidence_dict, breseq_folder):
    mutations_html = _get_beautifulsoup_html(breseq_folder, HTML_INDEX_FILE_NAME)
    mutation_rows = _get_unassigned_missing_coverage_rows(mutations_html)
    missing_coverage_dict = {}
    for row_num, row in enumerate(mutation_rows):
        attrs = row.findChildren("td")
        if not attrs:
            continue
        position = attrs[4].get_text()
        missing_coverage_dict[position] = [attrs[0].find("a")['href'],  # reads_left_url
                                           attrs[1].find("a")['href'],  # reads_right_url
                                           attrs[2].find("a")['href'],  # coverage
                                           attrs[6].get_text(),  # size
                                           attrs[7].get_text(),  # reads_left
                                           attrs[8].get_text(),  # reads_right
                                           attrs[9].get_text(),  # gene
                                           attrs[10].get_text()]  # description
    for key in evidence_dict:
        if _is_missing_coverage_type(evidence_dict[key]):
            # TODO: make literals into constants
            # Followed example given by ObservedMutations.
            # Seems like I have to use a mix of both Django and Alchemy ORM members.
            # Shouldn't have to do this.
            # TODO: Keyerrors only exist because the missing_coverage dict does not have the starting strain (wild type) html file
            try:
                html_attrs = missing_coverage_dict[str(evidence_dict[key]['start'])]
                UnassignedMissingCoverageEvidence.objects.get_or_create(seq_id=evidence_dict[key]['seq_id'],
                                                                        start=evidence_dict[key]['start'],
                                                                        end=evidence_dict[key]['end'],
                                                                        sequencing_experiment=seq_experiment,
                                                                        reads_left_url=html_attrs[0],
                                                                        reads_right_url=html_attrs[1],
                                                                        coverage=html_attrs[2],
                                                                        size=html_attrs[3],
                                                                        reads_left=html_attrs[4],
                                                                        reads_right=html_attrs[5],
                                                                        gene=html_attrs[6],
                                                                        description=html_attrs[7])
            except KeyError:
                UnassignedMissingCoverageEvidence.objects.create(seq_id=evidence_dict[key]['seq_id'],
                                                                 start=evidence_dict[key]['start'],
                                                                 end=evidence_dict[key]['end'],
                                                                 sequencing_experiment=seq_experiment)


def _parse_average_read_length(read_row_input):
    output = re.findall("\d+.\d+", read_row_input)[0]
    return output


def _parse_read_count(read_row_input):
    return int(read_row_input.replace(",", ""))


def _get_reseq_experiment_with_stats(breseq_folder, technical_replicate_id, person):
    breseq_path = ""
    index_file_path = breseq_folder + HTML_INDEX_FILE_NAME
    if os.path.isfile(index_file_path):
        breseq_path = breseq_folder[breseq_folder.find(ale_data_root_dir) + len(ale_data_root_dir):]
    reseq, created = ResequencingExperiment.objects.get_or_create(location=breseq_path,
                                                                  tech_rep_id=technical_replicate_id,
                                                                  person=person)
    statistics_html = _get_beautifulsoup_html(breseq_folder, HTML_SUMMARY_FILE_NAME)
    if statistics_html:
        row_read_info = statistics_html.find("tr", attrs={"class": "highlight_table_row"}).findChildren("td")
        reseq.reads = _parse_read_count(row_read_info[READ_COUNT_INDEX].text)
        reseq.average_read_length = _parse_average_read_length(row_read_info[AVERAGE_READ_LENGTH_INDEX].text)
        try:
            reseq.percentage_mapped = float(row_read_info[7].text.replace("%", ""))
        except:
            None
        # average coverage is 3rd table, 2nd row (could also be more rows), 5th column
        mean_coverage = statistics_html.findChildren("table")[2].findChildren("tr")[1].findChildren("td")[4].text
        try:
            mean_coverage = float(mean_coverage)
        except:
            mean_coverage = 0

        reseq.mean_coverage = mean_coverage

    reseq.save()
    return reseq


def _database_mutations(sample_type,
                        breseq_folder,
                        seq_experiment,
                        mutation_dict,
                        experiment,
                        is_wild_type):
    mutations_html = _get_beautifulsoup_html(breseq_folder, HTML_INDEX_FILE_NAME)
    column_type_index_dict = _get_mutation_header_dict(mutations_html)
    html_mut_resultset = _get_html_mutations_resultset(mutations_html, sample_type)
    observed_mutation_list = []

    # Only used if is_wild_type is True. Doesn't affect functionality otherwise
    # TODO: if this is the case, needs a conditional so not always executed.
    wild_type_mutation_list = []
    for mut_num in mutation_dict.keys():
        breseq_gene_annotation = mutation_dict[mut_num].get(GD_MUT_GENE_NAME_ATTR_KEY)
        breseq_gene_product_annotation = mutation_dict[mut_num].get(GD_MUT_GENE_PRODUCT_ATTR_KEY)
        gene_list = get_annotated_gene_list(breseq_gene_annotation, breseq_gene_product_annotation)
        gene_list_str = ', '.join(gene_list)
        sequence_change_str, protein_change_str = "", ""
        if GD_MUT_HTML in mutation_dict[mut_num].keys():
            # What is in the mutation HTML under the "mutation" column.
            bs_html = BeautifulSoup(mutation_dict[mut_num].get(GD_MUT_HTML), "lxml")
            sequence_change_str = bs_html.text.replace(u'\xa0', u' ').strip()
        if GD_MUT_ANNOTATION_HTML in mutation_dict[mut_num].keys():
            # What is in the mutation HTML under the "annotation" column.
            bs_html = BeautifulSoup(mutation_dict[mut_num].get(GD_MUT_ANNOTATION_HTML), "lxml")
            protein_change_str = bs_html.text.replace(u'\xa0', u' ').strip()
        mut, \
        created = Mutation.objects.get_or_create(position=mutation_dict[mut_num].get(GD_MUT_POS_ATTR_KEY),
                                                 gene=gene_list_str,
                                                 reseq_reference=mutation_dict[mut_num].get(GD_MUT_SEQ_ID_ATTR_KEY),
                                                 product=breseq_gene_product_annotation,
                                                 sequence_change=sequence_change_str,
                                                 mutation_type=mutation_dict[mut_num].get(GD_MUT_TYPE_ATTR_KEY),
                                                 protein_change=protein_change_str)
        mut.save()
        if is_wild_type is True:
            wild_type_mutation_list.append(mut.id)
        evidence = ""
        try:
            if html_mut_resultset:
                # mutations are in the same order in the html and output.gd
                # files so we can index the ids with row_num
                html_mut_idx = mut_num - 1
                html_row = html_mut_resultset[html_mut_idx]
                html_mut_attrs = html_row.findChildren("td")
                evidence = html_mut_attrs[column_type_index_dict[BRESEQ_REPORT_COLUMN_KEY_EVIDENCE]].renderContents()
        except:
            print("html_mut_resultset failed")
            e = sys.exc_info()[0]
            print("Error: %s" % e)
            traceback.print_exc()
        frequencies = _get_mutation_freq(mutation_dict[mut_num])

        observed_mutation = ObservedMutation(sequencing_experiment=seq_experiment,
                                             mutation=mut,
                                             breseq_present=True,
                                             evidence=evidence,
                                             frequency=frequencies[0],
                                             frequency_gatk=frequencies[1])
        observed_mutation_list.append(observed_mutation)

    ObservedMutation.objects.bulk_create(observed_mutation_list)

    if is_wild_type is True:
        exp_filter, created = AleExperimentFilter.objects.get_or_create(
            ale_experiment=experiment,
            defaults=filter.models.get_default_experiment_filter_params(experiment))
        exp_filter.starting_strain_mutations = ','.join(str(mut) for mut in wild_type_mutation_list)
        exp_filter.save()


def _get_mutation_freq(mutation_dict):
    frequency = DEFAULT_CLONAL_FREQ
    frequency_gatk = DEFAULT_GATK_FREQ

    if GD_MUT_FREQ_ATTR_KEY in mutation_dict:
        freq = mutation_dict[GD_MUT_FREQ_ATTR_KEY]
        if isinstance(freq, numbers.Number):
            frequency = freq
    for key in mutation_dict.keys():
        if key.startswith('frequency_'):
            if key.endswith('BRESEQ'):
                frequency = mutation_dict[key]
            elif key.endswith('GATK'):
                frequency_gatk = mutation_dict[key]


    return [frequency, frequency_gatk]


def _get_mutation_header_dict(mutations_html):
    header_dict = None
    if mutations_html:
        mutation_table = mutations_html.find("th", attrs={"class": "mutation_header_row"}).parent.parent
        table_header_rows = mutation_table.findChildren("th")
        header_dict = collections.defaultdict()
        for row_idx in range(1, len(table_header_rows)):
            column_name = table_header_rows[row_idx].getText()
            header_dict[column_name] = row_idx - 1
    return header_dict


def _get_html_mutations_resultset(mutations_html, sample_type):
    mutation_rows = None
    if mutations_html:
        # parse the mutation html file to find the correct table
        mutation_table = mutations_html.find("th", attrs={"class": "mutation_header_row"}).parent.parent
        if sample_type == gdparse.SampleType.CLONAL:
            html_class_to_parse = CLONAL_HTML_CLASSES_TO_PARSE_FOR_MUTATIONS
        else:
            html_class_to_parse = POPULATION_HTML_CLASSES_TO_PARSE_FOR_MUTATIONS
        mutation_rows = mutation_table.findChildren("tr", attrs={"class": html_class_to_parse})
    return mutation_rows


def _get_unassigned_missing_coverage_rows(mutations_html):
    try:
        mutation_table = mutations_html.find("th", attrs={"class": "missing_coverage_header_row"}).parent.parent

        mutation_rows = mutation_table.findChildren("tr")
    except AttributeError:
        mutation_rows = []

    return mutation_rows


def _find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""
