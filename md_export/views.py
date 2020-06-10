from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ale.utils import get_all_user_exps
from ale.permissions import can_view_project
from ale.models import Project
from zipfile import ZipFile
import io, csv
from md_export.util import get_md_csv_str
from logs.aledb_logger import user_extra
import logging

logger = logging.getLogger(__name__)


def md_export(request):
    logger.info("md_export", extra = user_extra(request))
    try:
        exp_id_str = request.GET.get('experiment_ids', None)
        project_id = request.GET.get('project_id', None)

        if project_id != 'null':
            project = get_object_or_404(Project, pk=int(project_id))
            if project and can_view_project(request.user, project):
                experiments = project.aleexperiment_set.all()
            else:
                return HttpResponse(status=403)
        else:
            experiments = get_all_user_exps(request.user)

        if exp_id_str:
            exp_list = []
            exp_id_list = exp_id_str.split(',')
            for exp in experiments:
                if str(exp.ale_id) in exp_id_list:
                    exp_list.append(exp)
            if len(exp_list) > 0:
                zip_data = io.BytesIO()
                zip_file = ZipFile(zip_data, 'w')
                for experiment in exp_list:
                    csv_data = io.StringIO()
                    writer = csv.writer(csv_data)
                    writer.writerows(get_md_csv_str(experiment))
                    csv_data.seek(0)
                    zip_file.writestr(experiment.name + '.csv', csv_data.read())
                zip_file.close()
                response = HttpResponse(zip_data.getvalue(), content_type='application/x-zip-compressed')
                response['Content-Disposition'] = 'attachment; filename="download.zip"'
                return response
        return HttpResponse(status=403)
    except Exception :
        logger.exception("md_export broke", extra = user_extra(request))
