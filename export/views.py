from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils.safestring import mark_safe
from django.core.serializers.json import DjangoJSONEncoder
from ale.utils import get_all_user_exps
from ale.permissions import can_view_project
from ale.models import AleExperiment, Project
import json
from export.util import get_csv_str
from logs.aledb_logger import user_extra
import logging

logger = logging.getLogger(__name__)


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
                context = {"project": project, "experiments": experiments}
                template = "ale/project_detail.html"
            else:
                return HttpResponse(status=403)
        else:
            experiments = get_all_user_exps(request.user)
            context = {"experiments": experiments}
            template = "ale/experiments_table.html"

        if mut_type_str and (project_id or exp_id_str):
            if exp_id_str:
                # print(str(datetime.now()), exp_name_str, mut_type_str)
                exp_id_list = exp_id_str.split(',')
                exp_list = []
                for exp_id in exp_id_list:
                    if len(exp_id) > 0:
                        exp = AleExperiment.objects.select_related("project").get(ale_id=exp_id)
                        if exp and can_view_project(request.user, exp.project):
                            exp_list.append(exp)
            elif project_id:
                exp_list = experiments

            if len(exp_list) > 0:
                    csv_str = [(get_csv_str(experiment.ale_id, mut_type_str), experiment.name + '_' + mut_type_str) for experiment in exp_list]
                    context['data'] = mark_safe(json.dumps(csv_str, cls=DjangoJSONEncoder))
                    context['is_download'] = True
                    return render(request, template, context)

        return HttpResponse(status=403)

    except Exception:
        logger.exception("export broke", extra = user_extra(request))

