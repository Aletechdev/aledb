from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
import aleinfo.settings as settings
from seq.util import get_all_observed_mutations
from seq.views import common
from filter import util
from stats.util import get_histogram_jsons,\
    get_needle_plot_data,\
    get_mutation_type_count_dict, \
    get_observed_mutation_type_count_dict,\
    get_protein_change_type_count_dict,\
    get_observed_protein_change_type_count_dict,\
    get_ale_flask_isolate_count_list,\
    get_reseq_experiment_info_list,\
    MAX_HISTOGRAM_SIZE
from common.util import get_reseq_queryset,\
    get_reseq_ordered_dict, get_mut_queryset_from_obs_mut_queryset, \
    get_all_ale_experiments, get_recent_experiments
from filter.util import filter_observed_mutations


__author__ = 'pphaneuf'

STATS_TEMPLATE = "stats/index.html"


# TODO: used by multiple views. Also implemented within ale_exp_filter.py; implement in one location.
if hasattr(settings, "sequencing_url"):
    resequencing_report_url = settings.sequencing_url


def stats(request):
    ale_experiment_id = common.get_ale_experiment_id(request)
    ale_id = common.get_ale_id(request)
    reseq_queryset = get_reseq_queryset(ale_experiment_id, ale_id)
    ale_flask_isolate_count_list = get_ale_flask_isolate_count_list(reseq_queryset)

    experiments_info_list = get_reseq_experiment_info_list(reseq_queryset)
    obs_mut_qryset = _get_observed_mutation_queryset(request, ale_experiment_id)
    mutation_query_set = get_mut_queryset_from_obs_mut_queryset(obs_mut_qryset)
    mutation_type_count_dict = get_mutation_type_count_dict(mutation_query_set)
    observed_mutation_type_count_dict = get_observed_mutation_type_count_dict(obs_mut_qryset)
    protein_change_type_count_dict = get_protein_change_type_count_dict(mutation_query_set)
    observed_protein_change_type_count_dict = get_observed_protein_change_type_count_dict(obs_mut_qryset)
    template = loader.get_template(STATS_TEMPLATE)
    ale_exp_name = common.get_ale_experiment_name(request)

    barchart_item_count = get_barchart_item_count(request)
    genes_json, sequence_change_json = get_histogram_jsons(obs_mut_qryset, barchart_item_count)

    needle_plot_data = get_needle_plot_data(obs_mut_qryset)
    context = {"protein_change_type_count_dict": protein_change_type_count_dict,
               "protein_change_sum": sum(protein_change_type_count_dict.values()),
               "observed_protein_change_type_count_dict": observed_protein_change_type_count_dict,
               "observed_protein_change_sum": sum(observed_protein_change_type_count_dict.values()),
               "mutation_type_count_dict": mutation_type_count_dict,
               "mutation_sum": sum(mutation_type_count_dict.values()),
               "observed_mutation_type_count_dict": observed_mutation_type_count_dict,
               "observed_mutation_sum": sum(observed_mutation_type_count_dict.values()),
               "experiments_info_list": experiments_info_list,
               "resequencing_report_url": resequencing_report_url,
               "ale_experiment_name": ale_exp_name,
               "needle_plot_data": mark_safe(list(needle_plot_data)),
               "genes": mark_safe(genes_json),
               "sequence_changes": mark_safe(sequence_change_json),
               "gene_color_set": mark_safe(common.GENE_COLORS),
               "seq_color_set": mark_safe(common.SEQ_COLORS),
               "mutation_types": mark_safe(common.MUTATION_TYPE_LIST),
               "protein_types": mark_safe(common.FUNCTIONAL_CHANGE_TYPE_LIST),
               "number_of_genes_to_show": barchart_item_count,
               "ale_experiment_id": ale_experiment_id,
               "ale_flask_isolate_count_list": ale_flask_isolate_count_list,
               "experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments(ale_experiment_id),
               "max_histogram_size": MAX_HISTOGRAM_SIZE}

    return HttpResponse(template.render(context))


def get_barchart_item_count(request):
    barchart_item_count = 20
    if 'number_of_top_genes' in request.GET:
        barchart_item_count_str = request.GET['number_of_top_genes']
        if barchart_item_count_str and barchart_item_count_str.isdigit():
            barchart_item_count = int(barchart_item_count_str)
    return barchart_item_count


# TODO: should be transferred to filter app and have a parameter to filter wt mutations.
def _get_observed_mutation_queryset(request, ale_experiment_id):
    ordered_reseq_dict = get_reseq_ordered_dict(ale_experiment_id)
    observed_mutation_query_set = get_all_observed_mutations(list(ordered_reseq_dict.keys()))
    observed_mutation_query_set = _exclude_ignored_genes_and_mutations(request, observed_mutation_query_set)
    return observed_mutation_query_set


# TODO: Should move this function into the filter app
def _exclude_ignored_genes_and_mutations(request, observed_mutation_query_set):
    # TODO: only filter out mutations without genes for the barcharts. The
    # mutations count tables above bar charts don't care if a mutation doesn't have a gene.
    # observed_mutation_query_set = observed_mutation_query_set.exclude(mutation__gene='')
    observed_mutation_query_set = observed_mutation_query_set.exclude()
    ale_experiment_id = common.get_ale_experiment_id(request)
    filter_settings = util.get_filter_settings(ale_experiment_id)
    observed_mutation_query_set = filter_observed_mutations(observed_mutation_query_set, filter_settings)
    return observed_mutation_query_set
