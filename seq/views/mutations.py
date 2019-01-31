import time
from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
import seq.views.common
from seq.views import mutation_table_builder
from seq.util import get_all_observed_mutations, get_reseq_ordered_dict
from ale.utils import get_recent_ale_exps, get_all_user_exps
from common.util import check_hidden_columns_and_filters, get_user_context
from common.constants import POSITION_COLUMN_IN_REGULAR_MUTATION_TABLE
from django.core.serializers.json import DjangoJSONEncoder
import json
import common.constants
from logs.aledb_logger import user_extra, join_extras
import logging

__author__ = 'pphaneuf'


logger = logging.getLogger(__name__)


def mutation_table(request):
    logger.info("mutation usage", user_extra(request))
    try:
        start_time = time.clock()
        context = get_user_context(request.user)
        experiment= seq.views.common.get_ale_experiment(request)

        exp_name = experiment.project.name + ": " + experiment.name
        ale_no = seq.views.common.get_ale_id(request)
        aleid_ale_id_list = seq.views.common.get_aleid_ale_id_list(experiment.ale_id, True)

        ordered_reseq_dict = get_reseq_ordered_dict(experiment.ale_id, ale_no, request)

        table_header = mutation_table_builder.get_table_header(request.user, ordered_reseq_dict)

        table_body = _get_table_body(ordered_reseq_dict, experiment, request.user)

        hidden_columns = check_hidden_columns_and_filters(request, experiment.ale_id)

        template = loader.get_template("base_table_template.html")

        context.update({"ales": aleid_ale_id_list,
                        "ale_experiment_name": exp_name,
                        "ale_no": ale_no,
                        "ale_experiment_id": experiment.ale_id,
                        "table_body": mark_safe(json.dumps(table_body, cls=DjangoJSONEncoder)),
                        "title": exp_name + " Mutations",
                        "table_header": table_header,
                        "template_header": "Mutations",
                        "hidden_columns": hidden_columns,
                        "recent_experiments": get_recent_ale_exps(experiment.ale_id),
                        "sorted_column": POSITION_COLUMN_IN_REGULAR_MUTATION_TABLE,
                        "tag_dropdown": common.constants.TAGS
                        })
        logger.info("mutation performance", extra=join_extras(user_extra(request), {"time taken": time.clock() - start_time}))

        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception as e:
        logger.exception("stats broke", extra=user_extra(request))
        template = loader.get_template("500.html")
        context['err_message'] = str(e)
        return HttpResponse(template.render(context, request), content_type="text/html")


def _get_table_body(reseq_dict, experiment, user):
    obs_mut_qryset = get_all_observed_mutations(list(reseq_dict.keys()))
    return mutation_table_builder.get_table_body(user, reseq_dict,
                                                 obs_mut_qryset,
                                                 experiment.ale_id)
