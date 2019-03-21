from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseForbidden
from ale.permissions import can_view_experiment
import logging
import os


DOC_ROOT = settings.ALE_DATA_ROOT_DIR

logger = logging.getLogger(__name__)


def protected_file_serve(request, page_name: str):
    """
    User can only view files in output folder. Make sure to handle files with binary data, e.g. images
    :param request:
    :param page_name:
    :return: the requested file or error if no permission or file link not available
    """
    user = request.user
    if len(page_name) > 0 and 'output/' in page_name:
        if page_name.endswith('output/'):
            reseq_location = page_name
        else:
            output_loc = page_name.find('output/')
            reseq_location = page_name[0:output_loc+len('output/')]
        ok = can_view_experiment(user, reseq_location)
        if not ok:
            logger.error("file path error: " + "Cannot view the link " + page_name)
            raise HttpResponseForbidden
        if page_name.endswith('/'):
            page_name = page_name + "index.html"
        logger.info("display file " + page_name)
        file_path = DOC_ROOT + page_name
        if os.path.isfile(file_path):
            mine_type = 'application/octet-stream'
            if file_path.endswith('txt') or file_path.endswith('.html') or file_path.endswith('.htm'):
                mine_type = 'text/html'
            elif file_path.endswith('.png'):
                mine_type = 'image/png'
            elif file_path.endswith('.pdf'):
                mine_type = 'application/pdf'
            with open(DOC_ROOT + page_name, 'rb') as f:
                response = HttpResponse(f.read(), content_type=mine_type)
            return response
    else:
        logger.error("file path error: " + "page not available - " + page_name)
        raise Http404

