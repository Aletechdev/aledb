from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseForbidden
from ale.permissions import can_view_experiment
import logging
import os

DOC_ROOT = settings.ALE_DATA_ROOT_DIR

logger = logging.getLogger(__name__)


def protected_file_serve(request, page_name: str):
    user = request.user
    if len(page_name) > 0 and '/' in page_name:
        slash_loc = page_name.rfind('/')
        reseq_location = page_name[0:slash_loc+1]
        ok = can_view_experiment(user, reseq_location)
        if not ok:
            logger.error("file path error: " + "Cannot view the link " + page_name)
            raise HttpResponseForbidden
    if page_name.endswith('/'):
        page_name = page_name + "index.html"
    logger.info("display file " + page_name)
    file_path = DOC_ROOT + page_name
    if os.path.isfile(file_path):
        with open(DOC_ROOT + page_name) as f:
            response = HttpResponse(f.read())
        return response
    else:
        logger.error("file path error: " + "page not available - " + page_name)
        raise Http404
