from django.views.static import serve
from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.shortcuts import render_to_response
from common.util import get_user_context
from ale.permissions import can_view_experiment
from logs.aledb_logger import get_logger
import logging
import os

DOC_ROOT = settings.ALE_DATA_ROOT_DIR
exception_lgr = get_logger("exceptions")
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
    logger.info("display file " + page_name)
    file_path = DOC_ROOT + page_name
    if os.path.isdir(file_path):
        file_list = os.listdir(file_path)
        template = 'file_list.html'
        context = get_user_context(user)
        context.update({'file_list': file_list})
        return render_to_response(template, context)
    elif os.path.isfile(file_path):
        with open(DOC_ROOT + page_name) as f:
            response = HttpResponse(f.read())
        return response
    else:
        logger.error("file path error: " + "page not available - " + page_name)
        raise Http404
