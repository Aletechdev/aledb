from os.path import join
import re
from bs4 import BeautifulSoup
from builder.gdparse.gdparse import gdparse
import collections
import csv
import numbers
import seq.models
import os
from configparser import ConfigParser
from genes.util import get_gene_list

HTML_SUMMARY_FILE_NAME = "summary.html"

HTML_MUTATION_FILE_NAME = "index.html"

CLONAL_HTML_CLASSES_TO_PARSE_FOR_MUTATIONS = ["normal_table_row"]

POPULATION_HTML_CLASSES_TO_PARSE_FOR_MUTATIONS = ["normal_table_row", "polymorphism_table_row"]

AVERAGE_READ_LENGTH_INDEX = 5

READ_COUNT_INDEX = 2

GD_MUT_POS_ATTR_KEY = 'position'

GD_MUT_GENE_NAME_ATTR_KEY = 'gene_name'

GD_MUT_TYPE_ATTR_KEY = 'type'

GD_MUT_FREQ_ATTR_KEY = 'frequency'

DEFAULT_CLONAL_FREQ = 1

BRESEQ_REPORT_COLUMN_KEY_EVIDENCE = "evidence"

BRESEQ_REPORT_COLUMN_KEY_POSITION = "position"

BRESEQ_REPORT_COLUMN_KEY_MUTATION = "mutation"

BRESEQ_REPORT_COLUMN_KEY_MUTATION_FREQUENCY = "freq"

BRESEQ_REPORT_COLUMN_KEY_ANNOTATION = "annotation"

BRESEQ_REPORT_COLUMN_KEY_GENE = "gene"

config = ConfigParser()
settings_file_path = os.path.join(os.path.dirname(__file__), "../aleinfo/settings.ini")
config.read(settings_file_path)
ale_data_root_dir = config.get("OTHER", "ale_data_root_dir")

DUPLICATION_BP_TOLERANCE = 900


def add_breseq_results(technical_replicate_id,
                       person,
                       breseq_folder,
                       ref_gene_list,
                       mutation_gd_parser,
                       annotation_gd_parser,
                       reseq_ref_name,
                       is_wild_type=False):
    """
    Figures out if the sample is clonal or population,
    and calls the appropriate "add" function.
    Read the output/log.txt file for " -p " option, which indicates that
    sample was processed as a population.
    """

    seq_experiment = _get_reseq_experiment_with_stats(breseq_folder,
                                                      technical_replicate_id,
                                                      person)

    sample_reseq_type = mutation_gd_parser.meta_data[gdparse.RESEQ_TYPE_KEY]

    sample_mutation_dict = mutation_gd_parser.data[gdparse.MUTATION_KEY]

    sample_mutation_annotation_dict = annotation_gd_parser.data[gdparse.MUTATION_KEY]

    _process_mutations(sample_reseq_type,
                       breseq_folder,
                       ref_gene_list,
                       seq_experiment,
                       sample_mutation_dict,
                       sample_mutation_annotation_dict,
                       reseq_ref_name,
                       is_wild_type)

    _process_duplications(breseq_folder,
                          ref_gene_list,
                          seq_experiment,
                          reseq_ref_name,
                          is_wild_type)

    sample_evidence_dict = mutation_gd_parser.data[gdparse.EVIDENCE_KEY]

    _process_unassigned_missing_coverage(seq_experiment,
                                         sample_evidence_dict,
                                         breseq_folder)


# TODO: remove unused reseq_reference argument.
def _process_duplications(breseq_folder,
                          ref_gene_list,
                          seq_experiment,
                          reseq_reference,
                          is_wild_type):


    afi = os.path.basename(os.path.dirname(os.path.dirname(breseq_folder)))

    # TODO: afi.startswith is not a valid approach. Need to find a way to determine wildtype if none is given
    if is_wild_type or afi.startswith('0'):
        return

    breseq_output_path = os.path.dirname(os.path.dirname(os.path.dirname(breseq_folder)))

    dup_path = breseq_output_path + "/dups/" + afi + "/" + afi + "_genes.csv"

    try:
        with open(dup_path, 'rt') as csvfile:

            duplications = list(csv.reader(csvfile, delimiter=','))

            if len(duplications) > 1:
                duplications.pop(0)
                observed_mutation_list = []
                for dup in duplications:

                    genes = list(csv.reader(dup[7].splitlines(), delimiter=','))[0]

                    if len(genes) <= 1:
                        gene_entry = _find_between(genes[0], "\'", "\'")
                    else:
                        gene_pair = [_find_between(genes[0], "\'", "\'"), _find_between(genes[-1], "\'", "\'")]
                        gene_entry = gene_pair[0] + "-" + gene_pair[1]

                    mutation, created = seq.models.Mutation.objects.get_or_create(position=dup[0],
                                                                                  gene=gene_entry,
                                                                                  sequence_change=(format(int(dup[2]), ",d") + " bp x" + dup[4]),
                                                                                  mutation_type="DUP")

                    mutation.protein_change = "Duplication"

                    mutation.save()

                    observed_mutation = seq.models.ObservedMutation(sequencing_experiment=seq_experiment,
                                                                    mutation=mutation,
                                                                    breseq_present=True,
                                                                    frequency=1.00)
                    observed_mutation_list.append(observed_mutation)

                seq.models.ObservedMutation.objects.bulk_create(observed_mutation_list)

    except IOError:
        return


# TODO: Keep this function around: has no current use but can be used to consolidate duplications into 1 mutation
def get_duplication_mutation(dup, gene_entry):

    exists = False

    mutations = seq.models.Mutation.objects.filter(position__gt=int(dup[0]) - DUPLICATION_BP_TOLERANCE,
                                                   position__lt=int(dup[0]) + DUPLICATION_BP_TOLERANCE,
                                                   gene=gene_entry,
                                                   mutation_type="DUP")

    # TODO: If count > 1 then should do more comparison to determine best match
    if mutations.count() > 0:
        mutation = mutations.first()
        exists = True
    else:

        mutation = seq.models.Mutation.objects.create(position=dup[0],
                                                      gene=gene_entry,
                                                      sequence_change=(format(int(dup[2]), ",d") + " bp x" + dup[4]),
                                                      mutation_type="DUP")

    return mutation, exists


def _get_beautifulsoup_html(output_folder, html_file_name):
    output_file_path = join(output_folder, html_file_name)

    with open(output_file_path) as infile:
        bs_html_file = BeautifulSoup(infile, "html.parser")

    return bs_html_file


def _is_missing_coverage_type(evidence_dict):
    is_missing_coverage = False

    if evidence_dict[gdparse.EVIDENCE_TYPE_KEY] == gdparse.MISSING_COVERAGE_EVIDENCE_TYPE:

        is_missing_coverage = True

    return is_missing_coverage


# Should be able to re-use this with populations.
def _process_unassigned_missing_coverage(seq_experiment, evidence_dict, breseq_folder):

    mutations_html = _get_beautifulsoup_html(breseq_folder, HTML_MUTATION_FILE_NAME)

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
                                           attrs[6].get_text(),         # size
                                           attrs[7].get_text(),         # reads_left
                                           attrs[8].get_text(),         # reads_right
                                           attrs[9].get_text(),         # gene
                                           attrs[10].get_text()]        # description

    for key in evidence_dict:

        if _is_missing_coverage_type(evidence_dict[key]):
            # TODO: make literals into constants
            # Followed example given by ObservedMutations.
            # Seems like I have to use a mix of both Django and Alchemy ORM members.
            # Shouldn't have to do this.

            # TODO: Keyerrors only exist because the missing_coverage dict does not have the starting strain (wild type) html file
            try:
                html_attrs = missing_coverage_dict[str(evidence_dict[key]['start'])]
                seq.models.UnassignedMissingCoverageEvidence.objects.get_or_create(seq_id=evidence_dict[key]['seq_id'],
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
                seq.models.UnassignedMissingCoverageEvidence.objects.create(seq_id=evidence_dict[key]['seq_id'],
                                                                            start=evidence_dict[key]['start'],
                                                                            end=evidence_dict[key]['end'],
                                                                            sequencing_experiment=seq_experiment)


def _parse_average_read_length(read_row_input):

    output = re.findall("\d+.\d+", read_row_input)[0]

    return output


def _parse_read_count(read_row_input):

    return int(read_row_input.replace(",", ""))


def _get_reseq_experiment_with_stats(breseq_folder, technical_replicate_id, person):

    seq_experiment, created = seq.models.ResequencingExperiment.objects.get_or_create(location=breseq_folder[breseq_folder.find(ale_data_root_dir) + len(ale_data_root_dir):],
                                                                                      tech_rep_id=technical_replicate_id,
                                                                                      person=person)

    statistics_html = _get_beautifulsoup_html(breseq_folder, HTML_SUMMARY_FILE_NAME)

    row_read_info = statistics_html.find("tr", attrs={"class": "highlight_table_row"}).findChildren("td")

    # if any mutations were read in, we need to overwrite them
    # ??? WHY ??? -Patrick
    # seq_experiment.mutations = []
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

    seq_experiment.save()

    return seq_experiment


# TODO: remove reseq_reference argument
def _process_mutations(sample_type,
                       breseq_folder,
                       ref_gene_list,
                       seq_experiment,
                       sample_mutation_dict,
                       sample_mutation_annotation_dict,
                       reseq_reference,
                       is_wild_type):

    mutations_html = _get_beautifulsoup_html(breseq_folder, HTML_MUTATION_FILE_NAME)

    column_type_index_dict = _get_mutation_header_dict(mutations_html)

    mutation_rows = _get_mutations_rows(mutations_html, sample_type)

    observed_mutation_list = []

    for row_num, row in enumerate(mutation_rows):

        mutation_num = row_num + 1  # row_num is 0 based, mutation_num is 1 based.

        attrs = row.findChildren("td")

        gene_annotation = str(sample_mutation_annotation_dict[mutation_num].get(GD_MUT_GENE_NAME_ATTR_KEY))
        gene_list = get_gene_list(gene_annotation, ref_gene_list)
        gene_list_str = ','.join(gene_list)

        mutation, created = seq.models.Mutation.objects.get_or_create(position=sample_mutation_dict[mutation_num].get(GD_MUT_POS_ATTR_KEY),
                                                                      gene=gene_list_str,
                                                                      # mutations are in the same order in the html and output.gd
                                                                      # files so we can index the ids with row_num
                                                                      sequence_change=attrs[column_type_index_dict[BRESEQ_REPORT_COLUMN_KEY_MUTATION]].text,
                                                                      mutation_type=sample_mutation_dict[mutation_num].get(GD_MUT_TYPE_ATTR_KEY))

        '''
        TODO: find out why this is used. I'm avoiding using it for now, since the mutation table won't the mutations
        for those samples which have this set to true.
        '''
        if is_wild_type:
            mutation.reference_error = True

        if mutation.protein_change is None:

            change = attrs[column_type_index_dict[BRESEQ_REPORT_COLUMN_KEY_ANNOTATION]].renderContents()
            mutation.protein_change = change

        mutation.save()

        observed_mutation = seq.models.ObservedMutation(sequencing_experiment=seq_experiment,
                                                        mutation=mutation,
                                                        breseq_present=True,
                                                        evidence=attrs[column_type_index_dict[BRESEQ_REPORT_COLUMN_KEY_EVIDENCE]].renderContents(),
                                                        frequency=_get_mutation_freq(sample_mutation_dict[mutation_num]))
        observed_mutation_list.append(observed_mutation)

    seq.models.ObservedMutation.objects.bulk_create(observed_mutation_list)


def _get_mutation_freq(mutation_dict):

    frequency = DEFAULT_CLONAL_FREQ

    # This will only execute if the sample is a population.
    if GD_MUT_FREQ_ATTR_KEY in mutation_dict:
        freq = mutation_dict[GD_MUT_FREQ_ATTR_KEY]
        if isinstance(freq, numbers.Number):
            frequency = freq

    return frequency


def _get_mutation_header_dict(mutations_html):

    mutation_table = mutations_html.find("th", attrs={"class": "mutation_header_row"}).parent.parent

    table_header_rows = mutation_table.findChildren("th")

    header_dict = collections.defaultdict()

    for row_idx in range(1, len(table_header_rows)):

        column_name = table_header_rows[row_idx].getText()
        header_dict[column_name] = row_idx - 1

    return header_dict


def _get_mutations_rows(mutations_html, sample_type):

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
