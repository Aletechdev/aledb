from django.http import HttpResponse

from common.util import get_user_context

from django.template import loader
from logs.aledb_logger import user_extra
from dashboard.models import ObservedMutationCounts, UniqueMutationCounts, SampleCounts
from dashboard.views import get_general_count_dict

import logging

from ale.models import AleExperiment


logger = logging.getLogger(__name__)


def get_unique_publication_count():
    return AleExperiment.objects.order_by().values('doi').distinct().count()


def home(request):

    # TODO: use the template location described within settings.py
    general_count_dict = get_general_count_dict()
    observed_mutation_counts = ObservedMutationCounts.objects.first()
    unique_mutation_counts = UniqueMutationCounts.objects.first()

    if unique_mutation_counts and observed_mutation_counts:
        general_count_dict['observed'] = observed_mutation_counts.total
        general_count_dict['unique'] = unique_mutation_counts.total

    context = get_user_context(request.user)
    context.update({"count_dict": general_count_dict,
                    "unique_mutation_counts": unique_mutation_counts,
                    "observed_mutation_counts": observed_mutation_counts})
    logger.info("home", extra=user_extra(request))
    context.update({"unique_publication_count": get_unique_publication_count})
    try:
        template = loader.get_template("home/index.html")

        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception:
        logger.exception("home broke", extra=user_extra(request))
