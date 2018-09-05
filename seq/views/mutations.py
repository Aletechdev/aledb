import time
from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
import seq.views.common
from seq.views import mutation_table_builder
from seq.util import get_all_observed_mutations
from common.util import common_context, get_recent_ale_exps, get_reseq_ordered_dict
from common.util import check_hidden_columns_and_filters
from common.constants import POSITION_COLUMN_IN_REGULAR_MUTATION_TABLE
from django.core.serializers.json import DjangoJSONEncoder
import json
import common.constants
from logs.aledb_logger import get_logger, user_extra, join_extras

__author__ = 'pphaneuf'


exception = get_logger("exceptions")
usage = get_logger("usage")
performance = get_logger("performance")


def mutation_table(request):
    usage.info("mutation", extra=user_extra(request))

    try:
        start_time = time.clock()
        ale_experiment_id = seq.views.common.get_ale_experiment_id(request)
        exp_name = seq.views.common.get_ale_experiment_name(request)
        ale_no = seq.views.common.get_ale_id(request)
        ale_queryset = seq.views.common.get_ales(ale_experiment_id, True)

        ordered_reseq_dict = get_reseq_ordered_dict(ale_experiment_id, ale_no, request)

        table_header = mutation_table_builder.get_table_header(request, ordered_reseq_dict)

        table_body = _get_table_body(ordered_reseq_dict, request)

        hidden_columns = check_hidden_columns_and_filters(request, ale_experiment_id)

        template = loader.get_template("base_table_template.html")

        context = common_context.copy()
        context.update({"ales": ale_queryset,
                   "ale_experiment_name": exp_name,
                   "ale_no": ale_no,
                   "ale_experiment_id": ale_experiment_id,
                   "table_body": mark_safe(json.dumps(table_body, cls=DjangoJSONEncoder)),
                   "title": exp_name + " Mutation Table",
                   "table_header": table_header,
                   "template_header": "Mutations",
                   "hidden_columns": hidden_columns,
                   "recent_experiments": get_recent_ale_exps(ale_experiment_id),
                   "sorted_column": POSITION_COLUMN_IN_REGULAR_MUTATION_TABLE,
                   "tag_dropdown": common.constants.TAGS
                   })
        performance.info("metadata performance", extra=join_extras(user_extra(request), {"time taken": time.clock()-start_time}))

        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception:
        exception.exception("mutations broke", extra=user_extra(request))


def _get_table_body(reseq_dict, request):
    obs_mut_qryset = get_all_observed_mutations(list(reseq_dict.keys()))
    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)
    return mutation_table_builder.get_table_body(request, reseq_dict,
                                                 obs_mut_qryset,
                                                 ale_experiment_id)
