import time
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.template import loader
from django.utils.safestring import mark_safe
from django.conf import settings
from seq.util import get_ordered_reseq_queryset
import seq.views.common
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
from common.util import get_user_context
from stats.util import get_observed_mutation_list
import logging
from bibliome.models import Publication
from logs.aledb_logger import user_extra, join_extras

logger = logging.getLogger(__name__)

__author__ = 'pphaneuf'
STATS_TEMPLATE = "stats.html"


# TODO: used by multiple views. Also implemented within ale_exp_filter.py; implement in one location.
if hasattr(settings, "SEQUENCING_URL"):
    resequencing_report_url = settings.SEQUENCING_URL


def stats(request):
    logger.info("stats usage", extra=user_extra(request))
    try:
        start_time = time.time()
        context = get_user_context(request.user)
        experiment = common.get_ale_experiment(request)
        if experiment:
            context.update(experiment.experiment_context())

        try:
            pub_qryset = Publication.objects.filter(ale_experiment=experiment)
        except Publication.DoesNotExist:
            pub_qryset = None

        experiment = seq.views.common.get_ale_experiment(request)
        exp_name = experiment.name
        ale_experiment_id = experiment.ale_id
        ale_number = seq.views.common.get_ale_id(request)

        ale_id = common.get_ale_id(request)
        reseq_queryset = get_ordered_reseq_queryset(experiment.ale_id, ale_id)
        ale_flask_isolate_count_list = get_ale_flask_isolate_count_list(reseq_queryset)
        ale_sum = len(ale_flask_isolate_count_list)
        flask_sum = 0
        isolate_sum = 0
        for l in ale_flask_isolate_count_list:
            flask_sum += l[1]
            isolate_sum += l[2]

        experiments_info_list = get_reseq_experiment_info_list(reseq_queryset)
        obs_mutations = get_observed_mutation_list(experiment.ale_id)
        mutations_dict = {obs_mut.mutation.id: obs_mut.mutation for obs_mut in obs_mutations}
        mutations = mutations_dict.values()
        mutation_type_count_dict = get_mutation_type_count_dict(mutations)
        observed_mutation_type_count_dict = get_observed_mutation_type_count_dict(obs_mutations)
        protein_change_type_count_dict = get_protein_change_type_count_dict(mutations)
        observed_protein_change_type_count_dict = get_observed_protein_change_type_count_dict(obs_mutations)
        template = loader.get_template(STATS_TEMPLATE)

        barchart_item_count = get_histogram_item_count(request)
        genes_json = get_histogram_jsons(experiment.ale_id, barchart_item_count)

        needle_plot_data = get_needle_plot_data(experiment.ale_id)
        context.update({"ale_experiment_name": exp_name,
                        "ale_no": ale_number,
                        "ale_experiment_id": ale_experiment_id,
                        "ale_project_name": experiment.project.name,
                        "ale_project_id": experiment.project.id,
                        "protein_change_type_count_dict": protein_change_type_count_dict,
                        "protein_change_sum": sum(protein_change_type_count_dict.values()),
                        "observed_protein_change_type_count_dict": observed_protein_change_type_count_dict,
                        "observed_protein_change_sum": sum(observed_protein_change_type_count_dict.values()),
                        "mutation_type_count_dict": mutation_type_count_dict,
                        "mutation_sum": sum(mutation_type_count_dict.values()),
                        "observed_mutation_type_count_dict": observed_mutation_type_count_dict,
                        "observed_mutation_sum": sum(observed_mutation_type_count_dict.values()),
                        "experiments_info_list": experiments_info_list,
                        "resequencing_report_url": resequencing_report_url,
                        "needle_plot_data": mark_safe(list(needle_plot_data)),
                        "genes": mark_safe(genes_json),
                        "gene_color_set": mark_safe(common.GENE_COLORS),
                        "seq_color_set": mark_safe(common.SEQ_COLORS),
                        "mutation_types": mark_safe(common.MUTATION_TYPE_LIST),
                        "protein_types": mark_safe(common.FUNCTIONAL_CHANGE_TYPE_LIST),
                        "number_of_genes_to_show": barchart_item_count,
                        "ale_flask_isolate_count_list": ale_flask_isolate_count_list,
                        "ale_sum": ale_sum,
                        "flask_sum": flask_sum,
                        "isolate_sum": isolate_sum,
                        "max_histogram_size": MAX_HISTOGRAM_SIZE,
                        "pub_qryset": pub_qryset,
                        "notes": experiment.notes,
                        })

        logger.info("stats performance",
                             extra=join_extras(user_extra(request), {"time taken": time.time() - start_time}))

        return HttpResponse(template.render(context, request), content_type="text/html")

    except Exception as e:
        logger.exception("stats broke", extra=user_extra(request))
        template = loader.get_template("500.html")
        context = get_user_context(request.user)
        context['err_message'] = str(e)
        return HttpResponse(template.render(context, request), content_type="text/html")


def get_histogram_item_count(request):
    barchart_item_count = 20
    if 'number_of_top_genes' in request.GET:
        barchart_item_count_str = request.GET['number_of_top_genes']
        if barchart_item_count_str and barchart_item_count_str.isdigit():
            barchart_item_count = int(barchart_item_count_str)
    return barchart_item_count
