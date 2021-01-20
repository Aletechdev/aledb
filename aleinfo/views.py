from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.template import loader
from ale.permissions import can_view_experiment
from ale.models import AleExperiment
from seq.models import ResequencingExperiment
from seq.views.common import get_ale_experiment
from logs.aledb_logger import user_extra
import logging
import os, json

DOC_ROOT = settings.ALE_DATA_ROOT_DIR
EXCLUDE_ALE_EXP_DIRS = ['bop27']

logger = logging.getLogger(__name__)

# list of data folders that the user can see. Key = user_id, val = list of dir paths
user_allowed_data_dirs = dict()


def protected_file_serve(request, page_name: str):
    """
    User can only view files in output folder. Make sure to handle files with binary data, e.g. images
    :param request:
    :param page_name:
    :return: the requested file or error if no permission or file link not available
    """
    user = request.user
    if page_name and 'output/' in page_name:
        if page_name.endswith('output/'):
            reseq_location = page_name
        else:
            output_loc = page_name.find('output/')
            reseq_location = page_name[0:output_loc + len('output/')]
        ok = can_view_experiment(user, reseq_location)
        if not ok:
            logger.error("file path error: " + "Cannot view the link " + page_name)
            raise HttpResponseForbidden
        if page_name.endswith('/'):
            page_name = page_name + "index.html"
        logger.info("display file " + page_name, extra=user_extra(request))
        file_path = DOC_ROOT + page_name
        return _get_file_response(file_path)
    if page_name and 'evidence' in page_name:
        if page_name.endswith('evidence/'):
            reseq_location = page_name
        else:
            output_loc = page_name.find('evidence/')
            reseq_location = page_name[0:output_loc + len('evidence/')]
        ok = can_view_experiment(user, reseq_location)
        if not ok:
            logger.error("file path error: " + "Cannot view the link " + page_name)
            raise HttpResponseForbidden
        logger.info("display file " + page_name, extra=user_extra(request))
        file_path = DOC_ROOT + page_name
        return _get_file_response(file_path)
    if '.html' in page_name:
        file_path = DOC_ROOT + page_name
        return _get_file_response(file_path)
    elif _is_valid_pagename(page_name, user):
        return _get_file_response(DOC_ROOT + page_name)
    else:
        logger.error("file path error: " + "page not available - " + page_name)
        raise Http404


def _get_file_response(file_path):
    if os.path.isfile(file_path):
        mine_type = 'application/octet-stream'
        if file_path.endswith('txt') or file_path.endswith('csv') or file_path.endswith('.html') or file_path.endswith(
                '.htm'):
            mine_type = 'text/html'
        elif file_path.endswith('.png'):
            mine_type = 'image/png'
        elif file_path.endswith('.pdf'):
            mine_type = 'application/pdf'
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=mine_type)
        return response
    else:
        Http404


def _is_valid_pagename(page_name, user):
    if user.id in user_allowed_data_dirs:
        allowed_dirs = user_allowed_data_dirs[user.id]
        for dir in allowed_dirs:
            if dir in page_name:
                return True
    return False


def show_amplifiction_data(request):
    try:
        experiment = get_ale_experiment(request)
        data_dirs = _get_exp_data_folder_name(experiment)
        amp_file_dirs = []
        for data_dir in data_dirs:
            dir1 = data_dir + "/amplifications/"
            dir2 = data_dir + "/breseq/dups/"
            dir = ''
            if os.path.isdir(DOC_ROOT + dir1):
                dir = dir1
            elif os.path.isdir(DOC_ROOT + dir2):
                dir = dir2
            if dir:
                file_list = os.listdir(DOC_ROOT + dir)
                file_url_dict = {}
                base_url = "/aledata/" + dir
                for file in file_list:
                    url = base_url + file + '/' + file + '.html'
                    amp_file_dirs.append(dir + file)
                    file_url_dict[file] = url
                if file_url_dict:
                    user_allowed_data_dirs[request.user.id] = amp_file_dirs
        if len(amp_file_dirs) > 0:
            template = loader.get_template('file_list.html')
            context = experiment.experiment_context()
            context.update({'file_urls': file_url_dict,
                            'subtitle': "Amplification Files",
                            'title': 'Amplifictions'})
            return HttpResponse(template.render(context, request), content_type="text/html")
        else:
            logger.error("file path error: " + "page not available - " + data_dir)
            raise Http404
    except Exception as ex:
        raise Http404


def _get_exp_data_folder_name(experiment: AleExperiment) -> []:
    reseqs = ResequencingExperiment.objects.filter(
        tech_rep__isolate__flask__ale_id__ale_experiment_id=experiment.ale_id)
    dirs = []
    for reseq in reseqs:
        if '/' in reseq.location:
            dir = reseq.location[:reseq.location.find('/breseq')]
            if dir not in dirs:
                dirs.append(dir)
    return dirs
