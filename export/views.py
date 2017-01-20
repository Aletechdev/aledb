from django.contrib.auth.decorators import login_required
from django.template import loader
from django.http import HttpResponse, StreamingHttpResponse
from common.db_util import get_all_ale_experiments, get_recent_experiments
from compare.views.common import get_ordered_reseq_dict_and_queryset
from ale.models import AleExperiment
from seq.views.mutation_table_builder import get_mutation_table_queryset_and_entry_list, HTML_MUTATION_TABLE_HEADER
import csv
from django.utils.html import strip_tags

import time

EXPORT_TEMPLATE = 'export.html'


class Echo(object):
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


@login_required
def export(request):

    experiment_names = request.GET.get('download_experiments', None)

    if experiment_names:

        if experiment_names == 'All':
            ale_experiment_list = [ale_exp.ale_id for ale_exp in AleExperiment.objects.all()]

        else:
            experiment_name_list = experiment_names.split(',')

            ale_experiment_list = [AleExperiment.objects.get(name=ale_exp_name).ale_id for ale_exp_name in experiment_name_list]

        print("Starting Process")

        start = time.time()
        total = time.time()

        ordered_reseq_dict, queryset = get_ordered_reseq_dict_and_queryset(ale_experiment_list)

        print("Generated Reseq Dict and Queryset in %s seconds" % get_elapsed_time(start))
        start = time.time()

        mutation_queryset, table_entry_list, mutation_index_dict = get_mutation_table_queryset_and_entry_list(
            ordered_reseq_dict, queryset, filter_settings=None)

        print("Got Mutation Table Queryset and Entry List in %s seconds" % get_elapsed_time(start))
        start = time.time()

        rows = [HTML_MUTATION_TABLE_HEADER[3:] + [ordered_reseq_dict[reseq].aleexp_ale_flask_isolate_str for reseq in ordered_reseq_dict]]

        print("Made Header Rows in %s seconds" % get_elapsed_time(start))
        print("Starting row generation for \033[92m%i\033[0m mutations" % len(mutation_queryset))
        start = time.time()

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

        print("Generated \033[92m%i\033[0m rows in %s seconds" % (len(mutation_queryset), get_elapsed_time(start)))

        pseudo_buffer = Echo()
        print("Echo")
        writer = csv.writer(pseudo_buffer)
        print("pseudo_buffer")
        response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
        print("Streaming Response")
        response['Content-Disposition'] = 'attachment; filename="database.csv"'
        print('Done!! Total time elapsed: %s' % get_elapsed_time(total))
        return response

    template = loader.get_template(EXPORT_TEMPLATE)

    context = {"experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments()
               }

    return HttpResponse(template.render(context))


def _strip_tags_from_list(frequencies):

    temp = []

    for frequency in frequencies:

        temp.append(strip_tags(frequency))

    return temp


def get_elapsed_time(start):

    return '\033[94m%.5f\033[0m' % (time.time() - start)
