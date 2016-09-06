from django.contrib.auth.decorators import login_required

from django.template import loader

from django.http import HttpResponse

from django.utils.safestring import mark_safe

from ale.models import AleExperiment

from filter.mutation_filter import dashboard_filter

from seq.models import ObservedMutation

from seq.views import mutation_table_builder

from common.db_util import get_reseq_queryset, get_all_ale_experiments, get_recent_experiments

from common.constants import REQUEST_ALL

import collections

from common.util import check_hidden_columns_and_filters

# Create your views here.


COMPARE_TEMPLATE = 'compare.html'

MUTATION_TABLE_TEMPLATE = 'mutation_table_template.html'

@login_required
def compare(request):

    all_experiments = get_all_ale_experiments()

    hidden_columns = check_hidden_columns_and_filters(request, None)

    if request.method == 'POST':

        first_exp_name = request.POST.get('first_exp', None)

        second_exp_name = request.POST.get('second_exp', None)

        if not first_exp_name or not second_exp_name:
            return _handle_get_response(all_experiments, hidden_columns)

        first_exp = AleExperiment.objects.get(name=first_exp_name)

        second_exp = AleExperiment.objects.get(name=second_exp_name)

        ale_experiment_list = [first_exp.ale_id, second_exp.ale_id]

        ordered_reseq_dict = _get_ordered_reseq_dict(ale_experiment_list)

        gene_query = ObservedMutation.objects.exclude(mutation__gene='').filter(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__ale_id__in=ale_experiment_list)

        queryset = dashboard_filter(gene_query, ale_experiment_list=ale_experiment_list)

        table_body = mutation_table_builder.get_table_body(ordered_reseq_dict,
                                                           queryset,
                                                           table_type=mutation_table_builder.TableType.COMPARE)

        table_header = mutation_table_builder.get_table_header(ordered_reseq_dict)

        title = "Comparison of %s and %s" % (first_exp_name, second_exp_name)

        context = {"experiments": all_experiments,
                   "experiment_id": "%s,%s" % (first_exp.ale_id, second_exp.ale_id),
                   "has_comparison": True,
                   "title": title,
                   "template_header": title,
                   "table_header": mark_safe(table_header),
                   "table_body": mark_safe(table_body),
                   "hidden_columns": hidden_columns,
                   "recent_experiments": get_recent_experiments()}

        template = loader.get_template(MUTATION_TABLE_TEMPLATE)

        return HttpResponse(template.render(context))

    # Else is GET

    return _handle_get_response(all_experiments, hidden_columns)


def _handle_get_response(all_experiments, hidden_columns):

    context = {"experiments": all_experiments,
               "has_comparison": False,
               "hidden_columns": hidden_columns,
               "recent_experiments": get_recent_experiments(None)}

    template = loader.get_template(COMPARE_TEMPLATE)

    return HttpResponse(template.render(context))


def _get_ordered_reseq_dict(ale_experiment_list):

    queryset = get_reseq_queryset(REQUEST_ALL)

    queryset = queryset.filter(tech_rep__isolate__flask__ale_id__ale_experiment__ale_id__in=ale_experiment_list)

    seq_experiment_ordered_dict = collections.OrderedDict()

    for reseq in queryset:
        seq_experiment_ordered_dict[reseq.id] = reseq

    return seq_experiment_ordered_dict
