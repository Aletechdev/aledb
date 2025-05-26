from django.http import HttpResponse
from django.http import StreamingHttpResponse
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
                def generate_zip():
                    zip_data = ZipStream(compress_type=ZIP_DEFLATED, compress_level=0)
                    for experiment in exp_list:
                        csv_buffer = io.BytesIO()
                        writer = csv.writer(io.TextIOWrapper(csv_buffer, encoding='utf-8', write_through=True))
                        writer.writerows(get_csv_str(experiment.ale_id, mut_type_str))
                        filename = f"{safe_filename(experiment.project.name)}_{safe_filename(experiment.name)}_{mut_type_str}.csv"
                        csv_bytes = csv_buffer.getvalue()
                        zip_data.add(csv_bytes, filename)
                        logger.info(f"Added {filename} to zip", extra=user_extra(request))
                    yield from zip_data
                response = StreamingHttpResponse(generate_zip(), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="download.zip"'
                return response
    except Exception :
        logger.exception("export broke", extra = user_extra(request))
        return HttpResponse("Internal server error during export.", status=500)
    # Catch any path that doesn't return explicitly
    return HttpResponse("Invalid export request.", status=400)
