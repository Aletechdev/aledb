from django.contrib.auth.decorators import login_required

from django.template import loader

from django.http import HttpResponse

from django.utils.safestring import mark_safe

from ale.models import AleExperiment

from common.db_util import get_all_ale_experiments, get_recent_experiments, get_mutation_queryset_from_obs_mut_queryset

from common.util import check_hidden_columns_and_filters

from compare.views.common import get_ordered_reseq_dict_and_queryset

from stats.views import get_reseq_experiment_info_list, get_ale_flask_isolate_count_list

from seq.views import common

from django.db.models import Count

# Create your views here.


COMPARE_TEMPLATE = 'compare.html'


# TODO: This needs to be refactored: shares quite a bit with the stats page
@login_required
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

    ordered_reseq_dict, observed_mutation_queryset = get_ordered_reseq_dict_and_queryset(ale_experiment_list)

    needle_plot_data = []

    for observed_mutation in observed_mutation_queryset:
        needle_plot_data.append(
            {'coord': str(observed_mutation.mutation.position), 'category': observed_mutation.mutation.mutation_type,
             'value': 1})

    experiments_info_list = get_reseq_experiment_info_list(ordered_reseq_dict.values())

    mutation_query_set = get_mutation_queryset_from_obs_mut_queryset(observed_mutation_queryset)

    mutation_type_count_dict = _get_mutation_type_count_dict(mutation_query_set)
    observed_mutation_type_count_dict = _get_observed_mutation_type_count_dict(observed_mutation_queryset)

    protein_change_type_count_dict = _get_protein_change_type_count_dict(mutation_query_set)
    observed_protein_change_type_count_dict = _get_observed_protein_change_type_count_dict(observed_mutation_queryset)

    ale_flask_isolate_count_list = get_ale_flask_isolate_count_list(ordered_reseq_dict.values())

    header = "Comparison of %s" % experiment_names.replace(",", ", ")

    gene_bar_chart_dict = common.get_gene_bar_chart_dict(observed_mutation_queryset, experiment_names)

    sequence_change_query = observed_mutation_queryset.values('mutation__gene', 'mutation__protein_change').annotate(
        the_count=Count('mutation__gene')).order_by('-the_count')

    genes = common.set_gene_bar_chart_colors(gene_bar_chart_dict)

    sequence_changes = common.set_sequence_change_bar_chart_colors(sequence_change_query)

    genes_to_show, sequence_changes_to_show, number_of_genes_to_show = common.get_genes_to_show(request, genes,
                                                                                                sequence_changes)

    context = {"experiments": all_experiments,
               "has_comparison": True,
               "ale_experiment_id": ale_experiment_list,
               "header": header,
               "genes": mark_safe(genes_to_show),
               "sequence_changes": mark_safe(sequence_changes_to_show),
               "gene_color_set": mark_safe(common.GENE_COLORS),
               "seq_color_set": mark_safe(common.SEQ_COLORS),
               "mutation_types": mark_safe(common.MUTATION_TYPE_LIST),
               "protein_types": mark_safe(common.FUNCTIONAL_CHANGE_TYPE_LIST),
               "number_of_genes_to_show": number_of_genes_to_show,
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


def _get_protein_change_type_count_dict(mutation_query_set):

    protein_change_type_count_dict = {}
    for protein_change_type in common.FUNCTIONAL_CHANGE_TYPE_LIST:
        protein_change_count = mutation_query_set.filter(protein_change__contains=protein_change_type).count()
        protein_change_type_count_dict[protein_change_type] = protein_change_count

    return protein_change_type_count_dict


def _get_observed_protein_change_type_count_dict(observed_mutations_query_set):

    protein_change_type_count_dict = {protein_change_type:0 for protein_change_type in common.FUNCTIONAL_CHANGE_TYPE_LIST}

    for observed_mutation in observed_mutations_query_set:
        for protein_change_type in common.FUNCTIONAL_CHANGE_TYPE_LIST:
            if protein_change_type in observed_mutation.mutation.protein_change:
                protein_change_type_count_dict[protein_change_type] += 1

    return protein_change_type_count_dict


def _get_mutation_type_count_dict(mutation_query_set):

    mutation_type_count_dict = {}
    for mutation_type in common.MUTATION_TYPE_LIST:
        mutation_type_count = mutation_query_set.filter(mutation_type=mutation_type).count()
        mutation_type_count_dict[mutation_type] = mutation_type_count

    return mutation_type_count_dict


def _get_observed_mutation_type_count_dict(observed_mutation_query_set):

    mutation_type_count_dict = {mutation_type:0 for mutation_type in common.MUTATION_TYPE_LIST}

    for observed_mutation in observed_mutation_query_set:
        mutation_type_count_dict[observed_mutation.mutation.mutation_type] += 1

    return mutation_type_count_dict


