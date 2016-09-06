from django.contrib.auth.decorators import login_required

from django.template import loader

from django.http import HttpResponse

from django.utils.safestring import mark_safe

from ale.models import AleExperiment

from seq.views import mutation_table_builder

from common.db_util import get_all_ale_experiments, get_recent_experiments

from common.util import check_hidden_columns_and_filters

from compare.views.common import get_ordered_reseq_dict_and_queryset

# Create your views here.


COMPARE_TEMPLATE = 'compare.html'

MUTATION_TABLE_TEMPLATE = 'mutation_table_template.html'


@login_required
def compared_mutations(request):

    all_experiments = get_all_ale_experiments()

    hidden_columns = check_hidden_columns_and_filters(request, None)

    first_exp_name = request.GET.get('first_exp', None)

    second_exp_name = request.GET.get('second_exp', None)

    first_exp = AleExperiment.objects.get(name=first_exp_name)

    second_exp = AleExperiment.objects.get(name=second_exp_name)

    ale_experiment_list = [first_exp.ale_id, second_exp.ale_id]

    ordered_reseq_dict, queryset = get_ordered_reseq_dict_and_queryset(ale_experiment_list)

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

