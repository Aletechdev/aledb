import collections

import ale.common

import ale.models

import seq.models

import re


__author__ = 'Patrick Phaneuf'


SETTINGS_SEQUENCING_URL = "sequencing_url"

DEFAULT_RESEQ_REPORT_URL = "http://localhost/sequencing/"

REQUEST_ALE_ID = "ale_no"

REQUEST_WT_FILTER = "wtfilt"

REQUEST_ALE_EXPERIMENT_ID = "ale_experiment_id"

REQUEST_ALL = "all"

ALE_NUMBER_SELECTOR_QUERY = "AND ale_no = %d"
ALE_EXPERIMENT_SELECTOR_QUERY = "AND experiment_id = %d"

SEQ_EXPERIMENT_QUERY = """SELECT reseq_id AS id FROM id_mapping WHERE reseq_id IS NOT NULL %s %s ORDER BY ale_no, flask_no, isolate_no ASC;"""

MUTATION_TYPE_LIST = ['SNP', 'SUB', 'DEL', 'INS', 'MOB', 'AMP', 'CON', 'INV', 'DUP', 'Default']

PROTEIN_CHANGE_TYPE_LIST = ['intergenic', 'noncoding', 'pseudogene', 'snp_type_synonymous', 'snp_type_nonsynonymous', 'Duplication', 'Default']

COLORS = ['red', 'black', 'blue', 'green', 'orange', 'grey', 'purple', 'olive', 'maroon']
DEFAULT_COLOR = 'steelblue'


def _set_colors(length):
    temp = COLORS[:length]
    temp.append(DEFAULT_COLOR)
    return temp


GENE_COLORS = _set_colors(len(MUTATION_TYPE_LIST) - 1)
SEQ_COLORS = _set_colors(len(PROTEIN_CHANGE_TYPE_LIST) - 1)


def get_ale_queryset(experiment_ids, exclude_starting_strain=False):

    if experiment_ids is not None:

        experiment = ale.models.AleExperiment.objects.get(ale_id=experiment_ids)

        experiment_queryset = experiment.aleid_set.only("ale_id")

    else:

        experiment_queryset = seq.models.ResequencingExperiment.objects.all()

    if exclude_starting_strain:

        experiment_queryset = experiment_queryset.exclude(ale_id=ale.common.STARTING_STRAIN_ALE_ID)

    return experiment_queryset


def get_wt_filter(request):

    ret_val = False

    if request.GET.get(REQUEST_WT_FILTER) is not None:
        ret_val = True

    return ret_val


def get_ale_number(request):

    ale_number = request.GET.get(REQUEST_ALE_ID)

    ale_number = None if ale_number is None or ale_number == "all" else int(ale_number)

    return ale_number


def get_ale_experiment_id(request):

    # Get the full list of ale experiments for the ale number of interest
    experiment_ids = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)

    experiment_ids = None if experiment_ids is None or experiment_ids == "all" else int(experiment_ids)

    return experiment_ids


def get_ale_experiment_name(request):

    ale_experiment_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)

    ale_experiment_name = "All ALE Experiments"

    if ale_experiment_id is not None and ale_experiment_id != "all":

        ale_experiment = ale.models.AleExperiment.objects.filter(ale_id=ale_experiment_id)

        # TODO: should only ever be returning 1 experiment. Implement error handling for more than one returned.
        ale_experiment_name = ale_experiment[0].name

    return ale_experiment_name


def get_ale_experiment_selector(ale_experiment_id):

    if ale_experiment_id is None or ale_experiment_id == REQUEST_ALL:

        ale_experiment_selector = ""

    else:

        ale_experiment_selector = ALE_EXPERIMENT_SELECTOR_QUERY % int(ale_experiment_id)

    return ale_experiment_selector


def get_ale_number_selector(ale_id):

    if ale_id is None or ale_id == REQUEST_ALL:

        ale_no_selector = ""

    else:

        ale_no_selector = ALE_NUMBER_SELECTOR_QUERY % int(ale_id)

    return ale_no_selector


def get_experiment_ordered_dict(request, include_starting_strain=False):

    seq_experiment_ordered_dict = collections.OrderedDict()

    if include_starting_strain:

        starting_strain_raw_queryset = _get_starting_string_mutation_queryset(request)

        for seq_experiment in starting_strain_raw_queryset:
            seq_experiment_ordered_dict[seq_experiment.id] = seq_experiment

    seq_experiments_raw_queryset = get_seq_experiment_raw_queryset(request)

    for seq_experiment in seq_experiments_raw_queryset:

        seq_experiment_ordered_dict[seq_experiment.id] = seq_experiment

    return seq_experiment_ordered_dict


def get_seq_experiment_raw_queryset(request):

    ale_id = request.GET.get(REQUEST_ALE_ID)

    return _get_seq_experiment_raw_queryset(request, ale_id)


def _get_starting_string_mutation_queryset(request):

    ale_id = ale.common.STARTING_STRAIN_ALE_ID

    return _get_seq_experiment_raw_queryset(request, ale_id)


def _get_seq_experiment_raw_queryset(request, ale_id):

    ale_experiment_id = request.GET.get(REQUEST_ALE_EXPERIMENT_ID)

    ale_experiment_selector = get_ale_experiment_selector(ale_experiment_id)

    ale_id_selector = get_ale_number_selector(ale_id)

    sql_query = SEQ_EXPERIMENT_QUERY % (ale_experiment_selector, ale_id_selector)

    seq_experiments_raw_queryset = seq.models.ResequencingExperiment.objects.raw(sql_query)

    return seq_experiments_raw_queryset


def get_observed_mutations(seq_experiment_id_list):

    observed_mutations = seq.models.ObservedMutation.objects.filter(sequencing_experiment_id__in=seq_experiment_id_list)

    return observed_mutations


def get_filter_settings(ale_experiment_id):

    filter_queryset = ale.models.Filter.objects.filter(ale_experiment_id=ale_experiment_id)

    if len(filter_queryset) is 0:
        return ale.models.Filter()

    filter_settings = filter_queryset[0]  # Since there's only one filter setting per experiment.

    return filter_settings


# TODO: Should only be one starting strain per ALE, therefore as soon as found, delete and exit. 
def filter_out_starting_strain_seq_experiment(seq_experiment_ordered_dict):

    key_to_delete_found = False

    key_to_delete = None

    for key, value in seq_experiment_ordered_dict.items():

        if value.ale_id == ale.common.STARTING_STRAIN_ALE_ID:

            key_to_delete = key

            key_to_delete_found = True

    if key_to_delete_found and key_to_delete:

        del seq_experiment_ordered_dict[key_to_delete]

    return seq_experiment_ordered_dict


def get_wt_seq_experiment_id(seq_experiment_ordered_dict):

    wt_id = None

    for key, value in seq_experiment_ordered_dict.items():

        if value.ale_id == ale.common.STARTING_STRAIN_ALE_ID:

            wt_id = key

    return wt_id


def get_ignored_genes(request, genes, sequence_changes):
    ignored_genes = request.GET.get('ignored_genes')
    gene_list = None
    if ignored_genes is not None:
        ignored_genes = ignored_genes.replace(" ", "").replace('\n', '').replace('\r', '').split(',')
        gene_list = ', '.join(ignored_genes)
        if len(ignored_genes) > 0 and ignored_genes[0] is not '':
            for g in ignored_genes:
                if str(g).startswith('*'):
                    genes = genes.exclude(mutation__gene__endswith=str(g)[1:])
                    sequence_changes = sequence_changes.exclude(mutation__gene__endswith=str(g)[1:])
                elif str(g).endswith('*'):
                    genes = genes.exclude(mutation__gene__startswith=str(g)[:-1])
                    sequence_changes = sequence_changes.exclude(mutation__gene__startswith=str(g)[:-1])
                else:
                    genes = genes.exclude(mutation__gene__contains=g)
                    sequence_changes = sequence_changes.exclude(mutation__gene__contains=g)

    return gene_list, genes, sequence_changes


def set_gene_bar_chart_colors(genes):
    for gene in genes:
        if gene['mutation__mutation_type'] in MUTATION_TYPE_LIST:
            gene['color'] = COLORS[MUTATION_TYPE_LIST.index(gene['mutation__mutation_type'])]
        else:
            gene['color'] = DEFAULT_COLOR
    return genes


def set_sequence_change_bar_chart_colors(sequence_changes):
    for seq_change in sequence_changes:
        has_match = False
        for protein in PROTEIN_CHANGE_TYPE_LIST:
            if protein in seq_change['mutation__protein_change']:
                seq_change['color'] = COLORS[PROTEIN_CHANGE_TYPE_LIST.index(protein)]
                has_match = True
                break
        if has_match is False:
            seq_change['color'] = DEFAULT_COLOR
        seq_change['mutation__protein_change'] = re.compile(r'<[^>]+>').sub('', seq_change['mutation__protein_change'])
    return sequence_changes


def get_genes_to_show(request, genes, sequence_changes):
    number_of_genes_to_show = 20

    if 'number_of_top_genes' in request.GET:

        number_of_genes = request.GET['number_of_top_genes']

        if _is_query_empty(number_of_genes):
            genes_to_show = list(genes[:number_of_genes_to_show])
            sequence_changes_to_show = list(sequence_changes[:number_of_genes_to_show])

        else:
            number_of_genes_to_show = request.GET['number_of_top_genes']
            genes_to_show = list(genes[:int(request.GET['number_of_top_genes'])])
            sequence_changes_to_show = list(sequence_changes[:int(request.GET['number_of_top_genes'])])

    else:
        genes_to_show = list(genes[:20])
        sequence_changes_to_show = list(sequence_changes[:20])

    return genes_to_show, sequence_changes_to_show, number_of_genes_to_show


def _is_query_empty(query):

    is_query_empty = False

    if not query:

        is_query_empty = True

    return is_query_empty
