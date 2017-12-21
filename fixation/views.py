from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
import seq.views.common
from seq.views import mutation_table_builder
from seq.models import ObservedMutation
from seq.models import ResequencingExperiment
from fixation.models import FixatedMutation
import metadata.views
from common.constants import \
    REQUEST_MUTATION_ID, \
    POSITION_COLUMN_IN_SHARED_MUTATION_TABLE, \
    POSITION_COLUMN_IN_ENRICH_OR_FIXED_MUT_TABLE
from common.util import get_reseq_ordered_dict,\
    get_all_ale_exps,\
    get_recent_ale_exps,\
    check_hidden_columns_and_filters
from collections import OrderedDict
from genes.util import get_gene_list
import operator
from functools import reduce
from django.db.models import Q
from fixation.util import get_exp_fixed_obs_mut_qryset
import common.constants
import ast


HTML_MUTATION_TABLE_HEADER = """<tr><td></td><td>Position</td><td>Mutation Type</td><td>Sequence Change</td><td>Gene</td><td>Function</td><td>Product</td><td>GO Process</td><td>GO Component</td><td>Details</td>"""

__author__ = 'Patrick Phaneuf'


def fixating_mutations(request):
    exp_name = seq.views.common.get_ale_experiment_name(request)
    exp_id = seq.views.common.get_ale_experiment_id(request)
    ale_number = seq.views.common.get_ale_id(request)
    ale_qryset = seq.views.common.get_ales(exp_id, True)

    reseq_ordered_dict = get_reseq_ordered_dict(exp_id, ale_number, request)

    table_header = mutation_table_builder.get_table_header(reseq_ordered_dict,
                                                           mutation_table_builder.TableType.FIXATING_MUTATIONS)

    obs_mut_qryset = get_exp_fixed_obs_mut_qryset(reseq_ordered_dict)

    table_body = mutation_table_builder.get_table_body(request, reseq_dict=reseq_ordered_dict,
                                                       observed_mutations_queryset=obs_mut_qryset,
                                                       ale_experiment_id=int(exp_id),
                                                       table_type=mutation_table_builder.TableType.FIXATING_MUTATIONS)

    hidden_columns = check_hidden_columns_and_filters(request, exp_id)

    template = loader.get_template("base_table_template.html")

    context = {"ales": ale_qryset,
               "ale_experiment_name": exp_name,
               "ale_no": ale_number,
               "experiment_id": exp_id,
               "table_body": mark_safe(table_body),
               "title": exp_name + " Fixed Mutations",
               "table_header": mark_safe(table_header),
               "template_header": "Fixating Mutations",
               "hidden_columns": hidden_columns,
               "experiments": get_all_ale_exps(),
               "recent_experiments": get_recent_ale_exps(int(exp_id)),
               "sorted_column": POSITION_COLUMN_IN_ENRICH_OR_FIXED_MUT_TABLE,
               "tag_dropdown": common.constants.TAGS}

    return HttpResponse(template.render(context, request), content_type="text/html")


def shared_fixated_mutations(request):
    mutation_id = request.GET.get(REQUEST_MUTATION_ID)
    selected_fixating_mutation_queryset = FixatedMutation.objects.filter(mutation_id=mutation_id)
    fixating_mutation = selected_fixating_mutation_queryset[0]  # Should only be one fixating mutation per mutation_id
    fixated_gene_str = fixating_mutation.mutation.gene
    fixated_gene_list = get_gene_list(fixated_gene_str)

    shared_fixated_gene_query = reduce(operator.or_, (Q(mutation__gene__contains=gene) for gene in fixated_gene_list))
    fixated_mutation_queryset = FixatedMutation.objects.filter(shared_fixated_gene_query)

    # fixated_mutation_ale_experiment_list = []
    ale_exp_fixed_obs_mut_id_list = []
    for fix_mut in fixated_mutation_queryset:
        # fixated_mutation_ale_experiment_list.append(fix_mut.ale_experiment)
        fixed_obs_mut_id_lists = list(ast.literal_eval(fix_mut.fixed_observed_mutation_series))  # Turns list of string into 2D list of observed mutation id lists.
        for fixed_obs_mut_id_list in fixed_obs_mut_id_lists:
            ale_exp_fixed_obs_mut_id_list = ale_exp_fixed_obs_mut_id_list + fixed_obs_mut_id_list

    observed_mutation_queryset = ObservedMutation.objects.filter(id__in=ale_exp_fixed_obs_mut_id_list)

    # observed_mutation_queryset = ObservedMutation.objects.filter(mutation__in=fixated_mutation_queryset.values('mutation'))
    # observed_mutation_queryset = observed_mutation_queryset.filter(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__in=fixated_mutation_ale_experiment_list)

    ordered_reseq_queryset = ResequencingExperiment.objects.all().order_by(
        'tech_rep__isolate__flask__ale_id__ale_experiment__name',
        'tech_rep__isolate__flask__ale_id__ale_id',
        'tech_rep__isolate__flask__flask_number',
        'tech_rep__isolate__isolate_number')
    ordered_reseq_queryset = ordered_reseq_queryset.filter(
        id__in=observed_mutation_queryset.values('sequencing_experiment'))

    ordered_reseq_dict = OrderedDict((reseq.id, reseq) for reseq in ordered_reseq_queryset)
    table_header = mutation_table_builder.get_table_header(ordered_reseq_dict)

    table_body = mutation_table_builder.get_table_body(request, ordered_reseq_dict,
                                                       observed_mutation_queryset,
                                                       table_type=mutation_table_builder.TableType.SHARED)

    reseq_info_list = metadata.views.get_reseq_info_list(ordered_reseq_queryset)

    check_hidden_columns_and_filters(request, None)

    template = loader.get_template("fixation/shared_fixating_mutations.html")
    context = {"title": "Shared Fixated Genes",
               "table_header": mark_safe(table_header),
               "table_body": mark_safe(table_body),
               "reseq_info_list": reseq_info_list,
               "experiments": get_all_ale_exps(),
               "recent_experiments": get_recent_ale_exps(),
               "sorted_column": POSITION_COLUMN_IN_SHARED_MUTATION_TABLE,
               }

    return HttpResponse(template.render(context, request), content_type="text/html")

