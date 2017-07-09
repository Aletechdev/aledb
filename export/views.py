from django.template import loader
from django.http import HttpResponse
from common.util import get_all_ale_experiments, get_recent_experiments
from compare.views.common import get_ordered_reseq_dict_and_queryset
from ale.models import AleExperiment
from seq.views.mutation_table_builder import get_mutation_table_queryset_and_entry_list, HTML_MUTATION_TABLE_HEADER
from django.utils.html import strip_tags
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.utils.safestring import mark_safe

EXPORT_TEMPLATE = 'export.html'


class Echo(object):
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def export(request):

    experiment_names = request.GET.get('download_experiments', None)

    context = {"experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments(),
               "is_download": False
               }

    if experiment_names:

        if experiment_names == 'All':
            ale_experiment_list = [(ale_exp.ale_id, ale_exp.name) for ale_exp in AleExperiment.objects.all()]

        else:
            experiment_name_list = experiment_names.split(',')

            ale_experiment_list = [(AleExperiment.objects.get(name=ale_exp_name).ale_id, ale_exp_name)
                                   for ale_exp_name in experiment_name_list]

        data = [(_get_rows_for_csv(exp_id), ale_exp_name) for exp_id, ale_exp_name in ale_experiment_list]
        context['data'] = mark_safe(json.dumps(data, cls=DjangoJSONEncoder))
        context['is_download'] = True

    template = loader.get_template(EXPORT_TEMPLATE)

    return HttpResponse(template.render(context))


def _strip_tags_from_list(frequencies):

    temp = []

    for frequency in frequencies:

        temp.append(strip_tags(frequency))

    return temp


def _get_rows_for_csv(exp_id):

    ordered_reseq_dict, queryset = get_ordered_reseq_dict_and_queryset([exp_id])

    mutation_queryset, table_entry_list, mutation_index_dict = get_mutation_table_queryset_and_entry_list(
        ordered_reseq_dict, queryset)

    rows = [HTML_MUTATION_TABLE_HEADER[3:] + [ordered_reseq_dict[reseq].aleexp_ale_flask_isolate_str
                                              for reseq in ordered_reseq_dict]]

    rows += ([format(mutation.position, ',d'),
              mutation.mutation_type,
              mutation.sequence_change,
              mutation.gene,
              "" if mutation.function is None else mutation.function,
              "" if mutation.product is None else mutation.product,
              "" if mutation.go_process is None else mutation.go_process,
              "" if mutation.go_component is None else mutation.go_component,
              strip_tags(mutation.protein_change)
              ] + _strip_tags_from_list(table_entry_list[mutation_index_dict[mutation.id]])
             for mutation in mutation_queryset)

    return rows
