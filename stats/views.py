import time
from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
from django.conf import settings
from seq.util import get_all_observed_mutations
from seq.views import common
from stats.util import get_histogram_jsons,\
    get_needle_plot_data,\
    get_mutation_type_count_dict, \
    get_observed_mutation_type_count_dict,\
    get_protein_change_type_count_dict,\
    get_observed_protein_change_type_count_dict,\
    get_ale_flask_isolate_count_list,\
    get_reseq_experiment_info_list,\
    MAX_HISTOGRAM_SIZE
from common.util import get_ordered_reseq_queryset,\
    get_reseq_ordered_dict, get_mut_queryset_from_obs_mut_queryset, \
    common_context, get_recent_ale_exps
from filter.util import get_filtered_observed_mutations_queryset
import ale.models
from bibliome.models import Publication
from logs.aledb_logger import get_logger, user_extra, join_extras

exception = get_logger("exceptions")
usage = get_logger("usage")
performance = get_logger("performance")

__author__ = 'pphaneuf'
STATS_TEMPLATE = "stats.html"


# TODO: used by multiple views. Also implemented within ale_exp_filter.py; implement in one location.
if hasattr(settings, "SEQUENCING_URL"):
    resequencing_report_url = settings.SEQUENCING_URL


def stats(request):
    usage.info("stats", extra = user_extra(request))
    try:
        start_time = time.clock()
        ale_experiment_id = common.get_ale_experiment_id(request)

        exp = ale.models.AleExperiment.objects.get(pk=ale_experiment_id)

        try:
            pub_qryset = Publication.objects.filter(ale_experiment=exp)
        except Publication.DoesNotExist:
            pub_qryset = None

        ale_id = common.get_ale_id(request)
        reseq_queryset = get_ordered_reseq_queryset(ale_experiment_id, ale_id)
        ale_flask_isolate_count_list = get_ale_flask_isolate_count_list(reseq_queryset)
        ale_sum = len(ale_flask_isolate_count_list)
        flask_sum = 0
        isolate_sum = 0
        for l in ale_flask_isolate_count_list:
            flask_sum += l[1]
            isolate_sum += l[2]

        experiments_info_list = get_reseq_experiment_info_list(reseq_queryset)
        obs_mut_qryset = _get_observed_mutation_queryset(request, ale_experiment_id)
        mutation_query_set = get_mut_queryset_from_obs_mut_queryset(obs_mut_qryset)
        mutation_type_count_dict = get_mutation_type_count_dict(mutation_query_set)
        observed_mutation_type_count_dict = get_observed_mutation_type_count_dict(obs_mut_qryset)
        protein_change_type_count_dict = get_protein_change_type_count_dict(mutation_query_set)
        observed_protein_change_type_count_dict = get_observed_protein_change_type_count_dict(obs_mut_qryset)
        template = loader.get_template(STATS_TEMPLATE)
        ale_exp_name = common.get_ale_experiment_name(request)

        barchart_item_count = get_histogram_item_count(request)
        genes_json = get_histogram_jsons(obs_mut_qryset, barchart_item_count)

        needle_plot_data = get_needle_plot_data(obs_mut_qryset)
        context = common_context.copy()
        context.update({"protein_change_type_count_dict": protein_change_type_count_dict,
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
                   "gene_color_set": mark_safe(common.GENE_COLORS),
                   "seq_color_set": mark_safe(common.SEQ_COLORS),
                   "mutation_types": mark_safe(common.MUTATION_TYPE_LIST),
                   "protein_types": mark_safe(common.FUNCTIONAL_CHANGE_TYPE_LIST),
                   "number_of_genes_to_show": barchart_item_count,
                   "ale_experiment_id": ale_experiment_id,
                   "ale_flask_isolate_count_list": ale_flask_isolate_count_list,
                   "ale_sum": ale_sum,
                   "flask_sum": flask_sum,
                   "isolate_sum": isolate_sum,
                   "recent_experiments": get_recent_ale_exps(ale_experiment_id),
                   "max_histogram_size": MAX_HISTOGRAM_SIZE,
                   "pub_qryset": pub_qryset,
                   "notes": exp.notes,
                   })
        performance.info("stats performance", extra=join_extras(user_extra(request), {"time taken": time.clock()-start_time}))

        return HttpResponse(template.render(context, request), content_type="text/html")

    except Exception:
        exception.exception("stats broke", extra = user_extra(request))


def get_histogram_item_count(request):
    barchart_item_count = 20
    if 'number_of_top_genes' in request.GET:
        barchart_item_count_str = request.GET['number_of_top_genes']
        if barchart_item_count_str and barchart_item_count_str.isdigit():
            barchart_item_count = int(barchart_item_count_str)
    return barchart_item_count


def _get_observed_mutation_queryset(request, ale_experiment_id):
    ordered_reseq_dict = get_reseq_ordered_dict(ale_experiment_id)
    observed_mutation_query_set = get_all_observed_mutations(list(ordered_reseq_dict.keys()))
    observed_mutation_query_set = get_filtered_observed_mutations_queryset(observed_mutation_query_set)
    return observed_mutation_query_set
