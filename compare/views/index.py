from django.template import loader
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from ale.models import AleExperiment
from common.util import check_hidden_columns_and_filters,\
    get_all_ale_experiments,\
    get_recent_experiments, \
    get_mut_queryset_from_obs_mut_queryset
from compare.views.common import get_ordered_reseq_dict_and_queryset
from seq.views import common
from stats.util import get_barchart_jsons,\
    get_needle_plot_data,\
    get_mutation_type_count_dict,\
    get_observed_mutation_type_count_dict,\
    get_protein_change_type_count_dict,\
    get_observed_protein_change_type_count_dict,\
    get_ale_flask_isolate_count_list,\
    get_reseq_experiment_info_list
from stats.views import get_barchart_item_count


COMPARE_TEMPLATE = 'compare.html'


def compare(request):
    all_experiments = get_all_ale_experiments()
    experiment_names = request.GET.get('download_experiments', None)
    if not experiment_names:
        hidden_columns = check_hidden_columns_and_filters(request, None)
        return handle_get_response(all_experiments, hidden_columns)

    # Else it is a valid request
    if experiment_names == 'All':
        ale_experiment_list = [ale_exp.ale_id for ale_exp in AleExperiment.objects.all()]
    else:
        experiment_name_list = experiment_names.split(',')
        ale_experiment_list = [AleExperiment.objects.get(name=ale_exp_name).ale_id for ale_exp_name in
                               experiment_name_list]

    # TODO: the below is very similar to stats.views.stats
    ordered_reseq_dict, obs_mut_qryset = get_ordered_reseq_dict_and_queryset(ale_experiment_list)
    needle_plot_data = get_needle_plot_data(obs_mut_qryset)
    experiments_info_list = get_reseq_experiment_info_list(ordered_reseq_dict.values())
    mutation_query_set = get_mut_queryset_from_obs_mut_queryset(obs_mut_qryset)
    mutation_type_count_dict = get_mutation_type_count_dict(mutation_query_set)
    observed_mutation_type_count_dict = get_observed_mutation_type_count_dict(obs_mut_qryset)
    protein_change_type_count_dict = get_protein_change_type_count_dict(mutation_query_set)
    observed_protein_change_type_count_dict = get_observed_protein_change_type_count_dict(obs_mut_qryset)
    ale_flask_isolate_count_list = get_ale_flask_isolate_count_list(ordered_reseq_dict.values())
    header = "Comparison of %s" % experiment_names.replace(",", ", ")

    barchart_item_count = get_barchart_item_count(request)
    genes_json, sequence_change_json = get_barchart_jsons(obs_mut_qryset, barchart_item_count)

    context = {"experiments": all_experiments,
               "has_comparison": True,
               "ale_experiment_id": ale_experiment_list,
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
               "recent_experiments": get_recent_experiments()}

    template = loader.get_template(COMPARE_TEMPLATE)

    return HttpResponse(template.render(context))


def handle_get_response(all_experiments, hidden_columns):

    context = {"experiments": all_experiments,
               "has_comparison": False,
               "hidden_columns": hidden_columns,
               "recent_experiments": get_recent_experiments(),
               "title": "Compare",
               "header": "Compare"}

    template = loader.get_template(COMPARE_TEMPLATE)

    return HttpResponse(template.render(context))
