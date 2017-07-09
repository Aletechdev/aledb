from django.template import loader
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from ale.models import AleExperiment
from seq.views import mutation_table_builder, common
from common.util import get_all_ale_experiments, get_recent_experiments, check_hidden_columns_and_filters
from compare.views.common import get_ordered_reseq_dict_and_queryset, get_ales_from_ale_experiment_list
from common.constants import POSITION_COLUMN_IN_REGULAR_MUTATION_TABLE, TAGS
import json
from django.core.serializers.json import DjangoJSONEncoder


MUTATION_TABLE_TEMPLATE = 'base_table_template.html'


def compared_mutations(request):

    hidden_columns = check_hidden_columns_and_filters(request, None)

    ale_no = common.get_ale_id(request)

    ale_experiment_string_list = request.GET.get('ale_experiment_id', None).replace(" ", "").replace('[', '').replace(']', '').split(',')

    ale_experiment_list = [int(exp_id) for exp_id in ale_experiment_string_list]

    ordered_reseq_dict, queryset = get_ordered_reseq_dict_and_queryset(ale_experiment_list, ale_no)

    table_body = mutation_table_builder.get_table_body(ordered_reseq_dict,
                                                       queryset,
                                                       table_type=mutation_table_builder.TableType.COMPARE)

    table_header = mutation_table_builder.get_table_header(ordered_reseq_dict)

    title = "%s Mutations" % (", ".join([AleExperiment.objects.get(ale_id=ale_exp_id).name for ale_exp_id in ale_experiment_list]))

    context = {"ales": get_ales_from_ale_experiment_list(ale_experiment_list),
               "ale_no": ale_no,
               "experiment_id": ale_experiment_list,
               "experiments": get_all_ale_experiments(),
               "title": "Mutation Table",
               "template_header": title,
               "table_header": mark_safe(table_header),
               "table_body": mark_safe(json.dumps(table_body, cls=DjangoJSONEncoder)),
               "hidden_columns": hidden_columns,
               "recent_experiments": get_recent_experiments(),
               "sorted_column": POSITION_COLUMN_IN_REGULAR_MUTATION_TABLE,
               "tag_dropdown": TAGS}

    template = loader.get_template(MUTATION_TABLE_TEMPLATE)

    return HttpResponse(template.render(context))

