from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

from common.util import get_user_context

from django.template import loader
from logs.aledb_logger import user_extra


def home(request):

    context = get_user_context(request.user)
    context.update({"count_dict": general_count_dict,
                    "unique_mutation_counts": unique_mutation_counts,
                    "observed_mutation_counts": observed_mutation_counts})
    user_projects = get_user_projects(request.user)
    context.update({"mut_types": MUT_TYPES,
                    "strains": STRAINS,
                    "ref_seqs": REF_SEQS,
                    "projects": user_projects})
    logger.info("home", extra=user_extra(request))
    context.update({"unique_publication_count": get_unique_publication_count})
    try:
        template = loader.get_template("home/index.html")

        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception:
        logger.exception("home broke", extra=user_extra(request))
