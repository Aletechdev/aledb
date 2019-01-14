import time

from django.http import HttpResponse

from django.template import loader

from django.conf import settings
from seq.views import common
from ale.utils import get_recent_ale_exps
from common.util import get_user_context
from seq.util import get_ordered_reseq_queryset

from common.constants import REQUEST_ALE_EXPERIMENT_ID, REQUEST_ALE_ID
from logs.aledb_logger import user_extra, join_extras
import logging

logger = logging.getLogger(__name__)

__author__ = 'Patrick Phaneuf'

# TODO: use the template location described within settings.py
META_DATA_TEMPLATE = "metadata/index.html"


# TODO: used by multiple views. Also implemented within ale_exp_filter.py; implement in one location.
if hasattr(settings, "SEQUENCING_URL"):
    reseq_report_url = settings.SEQUENCING_URL
else:
    reseq_report_url = common.DEFAULT_RESEQ_REPORT_URL


def metadata(request):
    logger.info("fixation usage", extra=user_extra(request))

    try:
        start_time = time.clock()
        context = get_user_context(request.user)
        experiment = common.get_ale_experiment(request)
        ale_experiment_id = experiment.ale_id
        ale_id = request.GET.get(REQUEST_ALE_ID)

        reseq_queryset = get_ordered_reseq_queryset(ale_experiment_id, ale_id)

        reseq_info_list = get_reseq_info_list(reseq_queryset)

        context = get_user_context(request.user)
        context.update({"reseq_info_list": reseq_info_list,
                        "reseq_report_url": reseq_report_url,
                        "ale_experiment_name": experiment.name,
                        "recent_experiments": get_recent_ale_exps(int(ale_experiment_id)),
                        "multiple": False,
                        "ale_experiment_id": ale_experiment_id
                        })

        template = loader.get_template(META_DATA_TEMPLATE)
        logger.info("metadata performance", extra=join_extras(user_extra(request), {"time taken": time.clock() - start_time}))
        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception as e:
        logger.exception("stats broke", extra=user_extra(request))
        template = loader.get_template("500.html")
        context['err_message'] = str(e)
        return HttpResponse(template.render(context, request), content_type="text/html")


def get_reseq_info_list(reseq_queryset):

    reseq_info_list = []

    for reseq in reseq_queryset:

        clonal_or_population = "clonal"
        if reseq.tech_rep.isolate.is_population:
            clonal_or_population = "population"

        experiment_info_tuple = (reseq,
                                 clonal_or_population,
                                 reseq.tech_rep.isolate.flask.media.temperature,
                                 reseq.tech_rep.isolate.flask.media.description,
                                 reseq.tech_rep.isolate.flask.media.substrate,
                                 reseq.tech_rep.isolate.flask.ale_id.strain,
                                 reseq.tech_rep.isolate.flask.ale_id.description,
                                 reseq.tech_rep.isolate.library_prep,
                                 reseq.tech_rep.isolate.reseq_reference,
                                 reseq.tech_rep.isolate.breseq_version,
                                 reseq.tech_rep.isolate.reseq_date,
                                 reseq.tech_rep.isolate.flask.ale_id.ale_experiment.name,
                                 reseq.tech_rep.description)

        reseq_info_list.append(experiment_info_tuple)

    return reseq_info_list
