import time
from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
import seq.views.common
from seq.views import mutation_table_builder
from seq.util import get_all_observed_mutations
from ale.utils import get_recent_ale_exps, get_all_ale_exps
from common.util import check_hidden_columns_and_filters, get_reseq_ordered_dict, get_user_context
from common.constants import POSITION_COLUMN_IN_REGULAR_MUTATION_TABLE
from django.core.serializers.json import DjangoJSONEncoder
import json
import common.constants
from logs.aledb_logger import get_logger, user_extra, join_extras

__author__ = 'pphaneuf'


exception_lgr = get_logger("exceptions")
usage_lgr = get_logger("usage")
performance_lgr = get_logger("performance")


def mutation_table(request):
    usage_lgr.info("mutation", extra=user_extra(request))

    try:
        start_time = time.clock()
        ale_experiment_id = seq.views.common.get_ale_experiment_id(request)
        exp_name = seq.views.common.get_ale_experiment_name(request)
        ale_no = seq.views.common.get_ale_id(request)
        aleid_ale_id_list = seq.views.common.get_aleid_ale_id_list(ale_experiment_id, True)

        ordered_reseq_dict = get_reseq_ordered_dict(ale_experiment_id, ale_no, request)

        table_header = mutation_table_builder.get_table_header(request, ordered_reseq_dict)

        table_body = _get_table_body(ordered_reseq_dict, request)

        hidden_columns = check_hidden_columns_and_filters(request, ale_experiment_id)

        template = loader.get_template("base_table_template.html")

        context = get_user_context(request.user)
        context.update({"ales": aleid_ale_id_list,
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
        performance_lgr.info("metadata performance", extra=join_extras(user_extra(request), {"time taken": time.clock() - start_time}))

        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception:
        exception_lgr.exception("mutations broke", extra=user_extra(request))


def _get_table_body(reseq_dict, request):
    obs_mut_qryset = get_all_observed_mutations(list(reseq_dict.keys()))
    ale_experiment_id = seq.views.common.get_ale_experiment_id(request)
    return mutation_table_builder.get_table_body(request, reseq_dict,
                                                 obs_mut_qryset,
                                                 ale_experiment_id)
