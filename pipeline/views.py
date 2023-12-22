# Create your views here.
from django.http import HttpResponse

from common.util import get_user_context

from django.template import loader
from logs.aledb_logger import user_extra
from pipeline.util import get_shared_directories, transfer_to_azure
from pipeline.azure_pipeline_util import run_pipeline
from pipeline.azure_upload_util import run_upload_script, get_output_directory_names, download_blobs_from_folder
from pipeline.models import get_runs

import logging

logger = logging.getLogger(__name__)


def manager(request):
    context = get_user_context(request.user)
    pipeline_runs = get_runs(request.user)
    context.update({"pipeline_runs": pipeline_runs})

    logger.info("pipeline_manager", extra=user_extra(request))

    if request.method == "POST":
        try:
            template = loader.get_template("pipeline/pipeline_manager.html")
            input_dir = request.POST['google_drive_folder']
            if len(str(input_dir)) > 5 and len(str(input_dir)) > 5:
                context.update({"response_text": request.POST})
                transfer_to_azure(input_dir)
            else:
                context.update({"error": "please input a longer directory name"})

            return HttpResponse(template.render(context, request), content_type="text/html")
        except Exception:
            logger.exception("pipeline manager broke", extra=user_extra(request))
    try:
        template = loader.get_template("pipeline/pipeline_manager.html")

        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception:
        logger.exception("pipeline manager broke", extra=user_extra(request))


def drive(request):
    logger.info("status", extra=user_extra(request))
    context = get_user_context(request.user)

    shared_directories_list = get_shared_directories()
    context.update({"shared_drives": shared_directories_list})

    if request.method == "POST":
        try:
            template = loader.get_template("pipeline/drive.html")
            input_dir = request.POST['google_drive_folder']
            if len(str(input_dir)) > 5 and len(str(input_dir)) > 5:
                context.update({"response_text": request.POST})
                transfer_to_azure(input_dir)
            else:
                context.update({"error": "please input a longer directory name"})

            return HttpResponse(template.render(context, request), content_type="text/html")
        except Exception:
            logger.exception("pipeline broke", extra=user_extra(request))
    try:
        template = loader.get_template("pipeline/drive.html")

        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception:
        logger.exception("pipeline drive broke", extra=user_extra(request))


def upload(request):
    # TODO: use the template location described within settings.py

    logger.info("upload", extra=user_extra(request))
    context = get_user_context(request.user)

    output_folders = get_output_directory_names()
    context.update({"output_folders": output_folders})

    if request.method == "POST":
        context.update({"response_text": request.POST})
        try:
            template = loader.get_template("pipeline/upload.html")
            download_blobs_from_folder(request.POST['azure_output_folder'])

            return HttpResponse(template.render(context, request), content_type="text/html")
        except Exception:
            logger.exception("webapp upload broke", extra=user_extra(request))
    try:
        template = loader.get_template("pipeline/upload.html")

        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception:
        logger.exception("webapp upload broke", extra=user_extra(request))


def pipeline(request):
    # TODO: use the template location described within settings.py

    logger.info("pipeline", extra=user_extra(request))
    context = get_user_context(request.user)

    # shared_directories_list = get_shared_directories()
    # context.update({"shared_drives": shared_directories_list})

    if request.method == "POST":
        try:
            template = loader.get_template("pipeline/pipeline.html")
            input_dir = request.POST['azure_data_folder']
            output_dir = request.POST['azure_output_folder']
            vm_size = request.POST['vm_size']
            if len(str(output_dir)) > 5 and len(str(input_dir)) > 5:
                context.update({"response_text": request.POST})
                run_pipeline(input_dir, output_dir, vm_size)
            else:
                context.update({"error": "please input a longer directory name"})

            return HttpResponse(template.render(context, request), content_type="text/html")
        except Exception:
            logger.exception("pipeline broke", extra=user_extra(request))
    try:
        template = loader.get_template("pipeline/pipeline.html")

        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception:
        logger.exception("pipeline broke", extra=user_extra(request))
