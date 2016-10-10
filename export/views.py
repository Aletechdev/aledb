from django.contrib.auth.decorators import login_required
from django.template import loader
from django.http import HttpResponse
from common.db_util import get_all_ale_experiments, get_recent_experiments
from compare.views.common import get_ordered_reseq_dict_and_queryset
from ale.models import AleExperiment
from seq.views.mutation_table_builder import get_table_body, get_table_header, TableType
from django.utils.safestring import mark_safe


EXPORT_TEMPLATE = 'export.html'


@login_required
def export(request):

    experiment_names = request.GET.get('download_experiments', None)

    is_download_request = False

    if experiment_names:

        is_download_request = True

        if experiment_names == 'All':
            ale_experiment_list = [ale_exp.ale_id for ale_exp in AleExperiment.objects.all()]

        else:
            experiment_name_list = experiment_names.split(',')

            ale_experiment_list = [AleExperiment.objects.get(name=ale_exp_name).ale_id for ale_exp_name in experiment_name_list]

        ordered_reseq_dict, queryset = get_ordered_reseq_dict_and_queryset(ale_experiment_list)

        table_header = get_table_header(ordered_reseq_dict)

        table_body = get_table_body(ordered_reseq_dict, queryset, table_type=TableType.SEARCH)

    else:

        table_body, table_header = "", ""

    template = loader.get_template(EXPORT_TEMPLATE)

    context = {"experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments(),
               "is_download_request": is_download_request,
               "table_body": mark_safe(table_body),
               "table_header": mark_safe(table_header)}

    return HttpResponse(template.render(context))
