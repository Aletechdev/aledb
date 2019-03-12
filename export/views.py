from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils.safestring import mark_safe
from django.core.serializers.json import DjangoJSONEncoder
from django_ajax.decorators import ajax
from ale.utils import get_all_user_exps
from ale.permissions import can_view_project
from ale.models import AleExperiment, Project
import json
from export.util import get_csv_str
from logs.aledb_logger import user_extra
import logging

logger = logging.getLogger(__name__)


@ajax
def export(request):
    logger.info("export", extra = user_extra(request))
    try:
        exp_id_str = request.GET.get('experiment_ids', None)
        mut_type_str = request.GET.get('mut_type', None)
        project_id = request.GET.get('project_id', None)

        if project_id:
            project = get_object_or_404(Project, pk=project_id)
            if project and can_view_project(request.user, project):
                experiments = project.aleexperiment_set.all()
            else:
                return HttpResponse(status=403)
        else:
            experiments = get_all_user_exps(request.user)

        if mut_type_str and exp_id_str:
            exp_list = []
            exp_id_list = exp_id_str.split(',')
            for exp in experiments:
                if str(exp.ale_id) in exp_id_list:
                    exp_list.append(exp)
            if len(exp_list) > 0:
                csv_str = [(experiment.name + '_' + mut_type_str, get_csv_str(experiment.ale_id, mut_type_str))for experiment in exp_list]
                text = mark_safe(json.dumps(csv_str, cls=DjangoJSONEncoder))
                return text
        return None
    except Exception:
        logger.exception("export broke", extra = user_extra(request))
