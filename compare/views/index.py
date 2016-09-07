from django.contrib.auth.decorators import login_required

from django.template import loader

from django.http import HttpResponse

from django.utils.safestring import mark_safe

from ale.models import AleExperiment

from common.db_util import get_all_ale_experiments, get_recent_experiments, get_mutation_queryset_from_observed_mutation_queryset

from common.util import check_hidden_columns_and_filters

from compare.views.common import get_ordered_reseq_dict_and_queryset

from stats.views import get_reseq_experiment_info_list, get_ale_flask_isolate_count_list

from seq.views import common

from django.db.models import Count

# Create your views here.


COMPARE_TEMPLATE = 'compare.html'


@login_required
def compare(request):

    all_experiments = get_all_ale_experiments()

    hidden_columns = check_hidden_columns_and_filters(request, None)

    first_exp_name = request.GET.get('first_exp', None)

    second_exp_name = request.GET.get('second_exp', None)

    if not first_exp_name or not second_exp_name:
        return handle_get_response(all_experiments, hidden_columns)

    first_exp = AleExperiment.objects.get(name=first_exp_name)

    second_exp = AleExperiment.objects.get(name=second_exp_name)

    ale_experiment_list = [first_exp.ale_id, second_exp.ale_id]

    ordered_reseq_dict, queryset = get_ordered_reseq_dict_and_queryset(ale_experiment_list)

    needle_plot_data = []

    for observed_mutation in queryset:
        needle_plot_data.append(
            {'coord': str(observed_mutation.mutation.position), 'category': observed_mutation.mutation.mutation_type,
             'value': 1})

    experiments_info_list = get_reseq_experiment_info_list(ordered_reseq_dict.values())

    mutation_query_set = get_mutation_queryset_from_observed_mutation_queryset(queryset)

    mutation_type_count_dict = _get_mutation_type_count_dict(mutation_query_set)
    observed_mutation_type_count_dict = _get_observed_mutation_type_count_dict(queryset)

    protein_change_type_count_dict = _get_protein_change_type_count_dict(mutation_query_set)
    observed_protein_change_type_count_dict = _get_observed_protein_change_type_count_dict(queryset)

    ale_flask_isolate_count_list = get_ale_flask_isolate_count_list(ordered_reseq_dict.values())

    title = "Comparison of %s and %s" % (first_exp_name, second_exp_name)

    gene_query = queryset.values('mutation__gene', 'mutation__mutation_type').annotate(
        the_count=Count('mutation__gene')).order_by('-the_count')
    sequence_change_query = queryset.values('mutation__gene', 'mutation__protein_change').annotate(
        the_count=Count('mutation__gene')).order_by('-the_count')

    genes = common.set_gene_bar_chart_colors(gene_query)

    sequence_changes = common.set_sequence_change_bar_chart_colors(sequence_change_query)

    genes_to_show, sequence_changes_to_show, number_of_genes_to_show = common.get_genes_to_show(request, genes,
                                                                                                sequence_changes)

    context = {"experiments": all_experiments,
               "experiment_id": "%s,%s" % (first_exp.ale_id, second_exp.ale_id),
               "has_comparison": True,
               "first_exp_name": first_exp_name,
               "second_exp_name": second_exp_name,
               "title": title,
               "header": title,
               "genes": mark_safe(genes_to_show),
               "sequence_changes": mark_safe(sequence_changes_to_show),
               "gene_color_set": mark_safe(common.GENE_COLORS),
               "seq_color_set": mark_safe(common.SEQ_COLORS),
               "mutation_types": mark_safe(common.MUTATION_TYPE_LIST),
               "protein_types": mark_safe(common.PROTEIN_CHANGE_TYPE_LIST),
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
               "recent_experiments": get_recent_experiments(None),
               "title": "Compare",
               "header": "Compare"}

    template = loader.get_template(COMPARE_TEMPLATE)

    return HttpResponse(template.render(context))


def _get_protein_change_type_count_dict(mutation_query_set):

    protein_change_type_count_dict = {}
    for protein_change_type in common.PROTEIN_CHANGE_TYPE_LIST:
        protein_change_count = mutation_query_set.filter(protein_change__contains=protein_change_type).count()
        protein_change_type_count_dict[protein_change_type] = protein_change_count

    return protein_change_type_count_dict


def _get_observed_protein_change_type_count_dict(observed_mutations_query_set):

    protein_change_type_count_dict = {protein_change_type:0 for protein_change_type in common.PROTEIN_CHANGE_TYPE_LIST}

    for observed_mutation in observed_mutations_query_set:
        for protein_change_type in common.PROTEIN_CHANGE_TYPE_LIST:
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


