from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
import seq.views.common
from seq.views import mutation_table_builder
from seq.util import get_all_observed_mutations
import filter.util
from common.db_util import get_all_ale_experiments, get_recent_experiments, get_reseq_ordered_dict
from common.util import check_hidden_columns_and_filters
from common.constants import POSITION_COLUMN_IN_REGULAR_MUTATION_TABLE
from django.core.serializers.json import DjangoJSONEncoder
import json
import common.constants

__author__ = 'pphaneuf'


def mutation_table(request):

    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)
    ale_experiment_name = seq.views.common.get_ale_experiment_name(request)
    ale_no = seq.views.common.get_ale_number(request)
    is_ref_strain_filtered = seq.views.common.is_ref_strain_filtered(request)
    ale_queryset = seq.views.common.get_ales(ale_experiment_id, is_ref_strain_filtered)

    ordered_reseq_dict = get_reseq_ordered_dict(ale_experiment_id, ale_no, request)

    table_header = mutation_table_builder.get_table_header(ordered_reseq_dict)

    table_body = _get_table_body(ordered_reseq_dict, request)

    hidden_columns = check_hidden_columns_and_filters(request, ale_experiment_id)

    template = loader.get_template("base_table_template.html")

    context = {"ales": ale_queryset,
               "ale_experiment_name": ale_experiment_name,
               "ale_no": ale_no,
               "experiment_id": ale_experiment_id,
               "table_body": mark_safe(json.dumps(table_body, cls=DjangoJSONEncoder)),
               "title": "Mutation Table",
               "table_header": table_header,
               "template_header": "Mutations",
               "wt_filter": is_ref_strain_filtered,
               "hidden_columns": hidden_columns,
               "experiments": get_all_ale_experiments(),
               "recent_experiments": get_recent_experiments(ale_experiment_id),
               "sorted_column": POSITION_COLUMN_IN_REGULAR_MUTATION_TABLE,
               "tag_dropdown": common.constants.TAGS
               }

    return HttpResponse(template.render(context))


def _get_table_body(reseq_dict, request):
    observed_mutations_query_set = get_all_observed_mutations(list(reseq_dict.keys()))
    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)
    filter_settings = filter.util.get_filter_settings(ale_experiment_id)
    return mutation_table_builder.get_table_body(reseq_dict,
                                                 observed_mutations_query_set,
                                                 ale_experiment_id,
                                                 filter_settings)
