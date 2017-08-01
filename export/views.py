from django.template import loader
from django.http import HttpResponse
from common.util import get_all_ale_exps, get_recent_ale_exps
from compare.views.common import get_ordered_reseq_dict_and_obs_mut_queryset
from ale.models import AleExperiment
from seq.views.mutation_table_builder import get_mutation_table_queryset_and_entry_list, HTML_MUTATION_TABLE_HEADER
from django.utils.html import strip_tags
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.utils.safestring import mark_safe


EXPORT_TEMPLATE = 'export.html'


def export(request):
    exp_name_str = request.GET.get('download_experiments', None)

    context = {
        "experiments": get_all_ale_exps(),
        "recent_experiments": get_recent_ale_exps(),
        "is_download": False
    }

    if exp_name_str:
        if exp_name_str == 'All':
            exp_list = [(exp.ale_id, exp.name) for exp in AleExperiment.objects.all()]
        else:
            exp_name_list = exp_name_str.split(',')
            exp_list = [(AleExperiment.objects.get(name=exp_name).ale_id, exp_name) for exp_name in exp_name_list]

        data = [(_get_rows_for_csv(ale_exp_id), ale_exp_name) for ale_exp_id, ale_exp_name in exp_list]
        context['data'] = mark_safe(json.dumps(data, cls=DjangoJSONEncoder))
        context['is_download'] = True

    template = loader.get_template(EXPORT_TEMPLATE)

    return HttpResponse(template.render(context))


def _get_rows_for_csv(exp_id):

    ordered_reseq_dict,\
    obs_mut_qryset = get_ordered_reseq_dict_and_obs_mut_queryset([exp_id])

    mut_qryset,\
    table_entry_list,\
    mut_index_dict = get_mutation_table_queryset_and_entry_list(ordered_reseq_dict, obs_mut_qryset)

    mut_pos_index = 3
    rows = [HTML_MUTATION_TABLE_HEADER[mut_pos_index:] + [ordered_reseq_dict[reseq].exp_ale_flask_isolate_str
                                              for reseq in ordered_reseq_dict]]

    rows += ([format(mutation.position, ',d'),
              mutation.mutation_type,
              mutation.sequence_change,
              mutation.gene,
              "" if mutation.function is None else mutation.function,
              "" if mutation.product is None else mutation.product,
              "" if mutation.go_process is None else mutation.go_process,
              "" if mutation.go_component is None else mutation.go_component,
              strip_tags(mutation.protein_change)] + _strip_tags_from_list(table_entry_list[mut_index_dict[mutation.id]])
             for mutation in mut_qryset)

    return rows


def _strip_tags_from_list(frequencies):
    temp = []
    for frequency in frequencies:
        temp.append(strip_tags(frequency))
    return temp