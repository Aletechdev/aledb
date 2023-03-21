import time
from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
import seq.views.common
from seq.views import mutation_table_builder
from common.constants import \
    REQUEST_MUTATION_ID, \
    REFSEQ_COLUMN_IN_MUT_TABLE
from common.util import get_user_context
from seq.util import get_reseq_ordered_dict
from fixation.util import get_fixed_obs_mut_qryset
import common.constants
from logs.aledb_logger import user_extra, join_extras
import logging


logger = logging.getLogger(__name__)

__author__ = 'Patrick Phaneuf'


def fixating_mutations(request):
    logger.info("fixation usage", extra=user_extra(request))

    try:
        start_time = time.clock()
        context = get_user_context(request.user)
        experiment = seq.views.common.get_ale_experiment(request)
        exp_name = experiment.name
        ale_experiment_id = experiment.ale_id
        ale_number = seq.views.common.get_ale_id(request)
        ale_qryset = seq.views.common.get_aleid_ale_id_list(ale_experiment_id, True)

        reseq_ordered_dict = get_reseq_ordered_dict(ale_experiment_id, ale_number, request)

        table_header = mutation_table_builder.get_table_header(request.user, reseq_ordered_dict, experiment)

        obs_mut_qryset = get_fixed_obs_mut_qryset(ale_experiment_id)

        table_body = mutation_table_builder.get_table_body(request.user, reseq_dict=reseq_ordered_dict,
                                                           observed_mutations_queryset=obs_mut_qryset,
                                                           ale_experiment=experiment,
                                                           is_gene_table=False)

        hidden_columns = request.GET.get('hidden_columns', "")

        template = loader.get_template("base_table_template.html")

        context.update({"ales": ale_qryset,
                        "ale_experiment_name": exp_name,
                        "ale_no": ale_number,
                        "ale_experiment_id": ale_experiment_id,
                        "ale_project_name": experiment.project.name,
                        "ale_project_id": experiment.project.id,
                        "table_body": mark_safe(table_body),
                        "title": exp_name + " Fixating Mutations",
                        "table_header": mark_safe(table_header),
                        "template_header": "Fixating Mutations",
                        "hidden_columns": hidden_columns,
                        "refseq_column": REFSEQ_COLUMN_IN_MUT_TABLE,
                        "tag_dropdown": common.constants.TAGS})

        logger.info("fixation performance",
                             extra=join_extras(user_extra(request), {"time taken": time.clock() - start_time}))
        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception as e:
        logger.exception("stats broke", extra=user_extra(request))
        template = loader.get_template("500.html")
        context['err_message'] = str(e)
        return HttpResponse(template.render(context, request), content_type="text/html")
