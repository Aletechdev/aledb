import re
import ale.common
import ale.models
import seq.models
from common.constants import REQUEST_ALE_EXPERIMENT_ID, REQUEST_ALE_ID

from django.core.cache import cache

from genes.util import get_gene_list

from operator import itemgetter

from collections import Counter


__author__ = 'Patrick Phaneuf'


SETTINGS_SEQUENCING_URL = "sequencing_url"

REQUEST_WT_FILTER = "wtflt"

MUTATION_TYPE_LIST = ['SNP', 'SUB', 'DEL', 'INS', 'MOB', 'DUP', 'AMP', 'CON', 'INV', 'Unannotated']

# Don't change these names since they match with Breseq's HTML annotations and used when parsing.
FUNCTIONAL_CHANGE_TYPE_LIST = ['intergenic', 'noncoding', 'pseudogene', 'snp_type_synonymous', 'snp_type_nonsynonymous', 'Duplication', 'Unannotated']

COLORS = ['#FF851B', '#2ECC40', '#0074D9', '#FFDC00', '#7FDBFF', '#B7337A', '#B10DC9', '#111111', '#85144b']

DEFAULT_COLOR = '#AAAAAA'


def _set_colors(length):
    temp = COLORS[:length]
    temp.append(DEFAULT_COLOR)
    return temp


GENE_COLORS = _set_colors(len(MUTATION_TYPE_LIST) - 1)
SEQ_COLORS = _set_colors(len(FUNCTIONAL_CHANGE_TYPE_LIST) - 1)

# TODO: change all instance of 'seq_experiment' to 'reseq'


def get_ales(experiment_ids, exclude_starting_strain=False):

    if experiment_ids is not None:

        experiment = ale.models.AleExperiment.objects.get(ale_id=experiment_ids)

        experiment_queryset = experiment.aleid_set.only("ale_id")

    else:

        experiment_queryset = seq.models.ResequencingExperiment.objects.all()

    if exclude_starting_strain:

        experiment_queryset = experiment_queryset.exclude(ale_id=ale.common.STARTING_STRAIN_ALE_ID)

    experiment_queryset_list = [exp.ale_id for exp in experiment_queryset]

    return experiment_queryset_list


def is_ref_strain_filtered(request):

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


# TODO: Should only be one starting strain per ALE, therefore as soon as found, delete and exit.
def filter_out_wt_reseq(reseq_ordered_dict):

    key_to_delete_found = False

    key_to_delete = None

    for key, value in reseq_ordered_dict.items():

        if value.ale_id == ale.common.STARTING_STRAIN_ALE_ID:

            key_to_delete = key

            key_to_delete_found = True

    if key_to_delete_found and key_to_delete:

        del reseq_ordered_dict[key_to_delete]

    return reseq_ordered_dict


def get_wt_reseq_id(seq_experiment_ordered_dict):

    wt_id = None

    for key, value in seq_experiment_ordered_dict.items():

        if value.ale_id == ale.common.STARTING_STRAIN_ALE_ID:

            wt_id = key

    return wt_id


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
        for protein in FUNCTIONAL_CHANGE_TYPE_LIST:
            if protein in seq_change['mutation__protein_change']:
                seq_change['color'] = COLORS[FUNCTIONAL_CHANGE_TYPE_LIST.index(protein)]
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


def get_gene_bar_chart_dict(observed_mutation_queryset, page):

    cache_string = page + '_bar_chart_gene_dict'

    cached_bar_chart_gene_dict = cache.get(cache_string)

    if cached_bar_chart_gene_dict is None:

        gene_list = [[get_gene_list(gene['mutation__gene']), gene['mutation__mutation_type']] for
                     gene in observed_mutation_queryset.values('mutation__gene', 'mutation__mutation_type')]

        mutation_type_gene_dict = {}

        for pair in gene_list:
            genes = set(pair[0])
            try:
                mutation_type_gene_dict[pair[1]] += [genes]
            except KeyError:
                mutation_type_gene_dict[pair[1]] = [genes]

        final_list = []

        for key, value in mutation_type_gene_dict.items():

            flattened_list = sorted([item for sublist in value for item in sublist], reverse=True)

            counted_list = Counter(flattened_list)

            for k, v in counted_list.items():

                new_dict = {'mutation__gene': k, 'the_count': v, 'mutation__mutation_type': key}

                final_list.append(new_dict)

        final_sorted_list = sorted(final_list, key=itemgetter('the_count'), reverse=True)

        cache.set(cache_string, final_sorted_list, None)

        return final_sorted_list

    return cached_bar_chart_gene_dict
