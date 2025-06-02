from django.http import HttpResponse
from zipstream import ZipStream, ZIP_DEFLATED
from django.shortcuts import get_object_or_404
from ale.utils import get_all_user_exps
from ale.permissions import can_view_project
from ale.models import Project
from zipfile import ZipFile
import io, csv
from export.util import get_csv_str
from logs.aledb_logger import user_extra
import logging
import re
from tempfile import NamedTemporaryFile
from django.http import FileResponse
import os
import zipfile

logger = logging.getLogger(__name__)

def safe_filename(name):
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)

def export(request):
    logger.info("export", extra = user_extra(request))
    try:
        exp_id_str = request.GET.get('experiment_ids', None)
        mut_type_str = request.GET.get('mut_type', None)
        project_id = request.GET.get('project_id', None)

        if project_id != 'null':
            project = get_object_or_404(Project, pk=int(project_id))
            if project and can_view_project(request.user, project):
                experiments = project.aleexperiment_set.all()
            else:
                return HttpResponse(status=403)
        else:
            experiments = get_all_user_exps(request.user)

        if mut_type_str and exp_id_str:
            exp_id_set = set(exp_id_str.split(','))
            exp_list = [exp for exp in experiments if str(exp.ale_id) in exp_id_set]
            if len(exp_list) > 0:
                tmp_file = NamedTemporaryFile(delete=False, suffix=".zip")
                try:
                    with zipfile.ZipFile(tmp_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for experiment in exp_list:
                            csv_buffer = io.StringIO()
                            writer = csv.writer(csv_buffer)
                            writer.writerows(get_csv_str(experiment.ale_id, mut_type_str))
                            filename = f"Proj_{safe_filename(experiment.project.name)}_Exp_{safe_filename(experiment.name)}_{mut_type_str}.csv"
                            zf.writestr(filename, csv_buffer.getvalue())
                            logger.info(f"Added {filename} to zip", extra=user_extra(request))

                    tmp_file.seek(0)
                    response = FileResponse(open(tmp_file.name, 'rb'), content_type='application/zip')
                    response['Content-Disposition'] = 'attachment; filename="download.zip"'

                    # Schedule cleanup
                    def cleanup(file_path):
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            logger.warning(f"Could not delete temp file {file_path}: {e}")

                    response.close = lambda close=response.close: (close(), cleanup(tmp_file.name))
                    return response

                except Exception:
                    logger.exception("export broke", extra=user_extra(request))
                    return HttpResponse("Internal server error during export.", status=500)
    except Exception :
        logger.exception("export broke", extra = user_extra(request))
        return HttpResponse("Internal server error during export.", status=500)
    # Catch any path that doesn't return explicitly
    return HttpResponse("Invalid export request.", status=400)
