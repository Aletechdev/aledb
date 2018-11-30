from django.template import loader
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from ale.models import AleExperiment
from ale.utils import get_all_ale_exps, get_recent_ale_exps
from common.util import check_hidden_columns_and_filters,\
    get_mut_queryset_from_obs_mut_queryset, get_user_context
from combine.views.common import get_ordered_reseq_dict_and_obs_mut_queryset
from seq.views import common
from stats.util import get_histogram_jsons,\
    get_needle_plot_data,\
    get_mutation_type_count_dict,\
    get_observed_mutation_type_count_dict,\
    get_protein_change_type_count_dict,\
    get_observed_protein_change_type_count_dict,\
    get_ale_flask_isolate_count_list,\
    get_reseq_experiment_info_list,\
    MAX_HISTOGRAM_SIZE
from stats.views import get_histogram_item_count


COMBINE_TEMPLATE = 'combine.html'


def combine(request):
    ale_exp_names = request.GET.get('download_experiments', None)
    if not ale_exp_names:
        return handle_initial_combine_form(request)
    else:
        return handle_combine_report(request, ale_exp_names)


def handle_combine_report(request, ale_experiment_names):
    all_ale_exp_qryset = get_all_ale_exps(request.user)

    # Else it is a valid request
    if ale_experiment_names == 'All':
        ale_exp_id_list = [ale_exp.ale_id for ale_exp in AleExperiment.objects.all()]
    else:
        experiment_name_list = ale_experiment_names.split(',')
        ale_exp_id_list = [AleExperiment.objects.get(name=ale_exp_name).ale_id for ale_exp_name in
                               experiment_name_list]

    # TODO: the below is very similar to stats.views.stats
    ordered_reseq_dict, obs_mut_qryset = get_ordered_reseq_dict_and_obs_mut_queryset(ale_exp_id_list)
    needle_plot_data = get_needle_plot_data(obs_mut_qryset)
    experiments_info_list = get_reseq_experiment_info_list(ordered_reseq_dict.values())
    mutation_query_set = get_mut_queryset_from_obs_mut_queryset(obs_mut_qryset)
    mutation_type_count_dict = get_mutation_type_count_dict(mutation_query_set)
    observed_mutation_type_count_dict = get_observed_mutation_type_count_dict(obs_mut_qryset)
    protein_change_type_count_dict = get_protein_change_type_count_dict(mutation_query_set)
    observed_protein_change_type_count_dict = get_observed_protein_change_type_count_dict(obs_mut_qryset)
    ale_flask_isolate_count_list = get_ale_flask_isolate_count_list(ordered_reseq_dict.values())
    header = "Comparison of %s" % ale_experiment_names.replace(",", ", ")

    barchart_item_count = get_histogram_item_count(request)
    genes_json, sequence_change_json = get_histogram_jsons(obs_mut_qryset, barchart_item_count)

    context = get_user_context(request.user)
    context.update({"has_comparison": True,
               "ale_experiment_id": ale_exp_id_list,
               "header": header,
               "genes": mark_safe(genes_json),
               "sequence_changes": mark_safe(sequence_change_json),
               "gene_color_set": mark_safe(common.GENE_COLORS),
               "seq_color_set": mark_safe(common.SEQ_COLORS),
               "mutation_types": mark_safe(common.MUTATION_TYPE_LIST),
               "protein_types": mark_safe(common.FUNCTIONAL_CHANGE_TYPE_LIST),
               "number_of_genes_to_show": barchart_item_count,
               "experiments_info_list": experiments_info_list,
               "needle_plot_data": mark_safe(list(needle_plot_data)),
               "protein_change_type_count_dict": protein_change_type_count_dict,
               "observed_protein_change_type_count_dict": observed_protein_change_type_count_dict,
               "mutation_type_count_dict": mutation_type_count_dict,
               "observed_mutation_type_count_dict": observed_mutation_type_count_dict,
               "ale_flask_isolate_count_list": ale_flask_isolate_count_list,
               "download_experiments": ale_experiment_names,
               "max_histogram_size": MAX_HISTOGRAM_SIZE})

    template = loader.get_template(COMBINE_TEMPLATE)

    return HttpResponse(template.render(context, request), content_type="text/html")


def handle_initial_combine_form(request):
    all_ale_exp_qryset = get_all_ale_exps(request.user)
    hidden_columns = check_hidden_columns_and_filters(request, None)
    context = {"experiments": all_ale_exp_qryset,
               "has_comparison": False,
               "hidden_columns": hidden_columns,
               "recent_experiments": get_recent_ale_exps(),
               "title": "Combine",
               "header": "Combine"}
    template = loader.get_template(COMBINE_TEMPLATE)
    return HttpResponse(template.render(context, request), content_type="text/html")
