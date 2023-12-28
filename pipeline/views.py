# Create your views here.
from django.http import HttpResponse

from common.util import get_user_context

from django.template import loader
from django.contrib.auth.decorators import login_required
from logs.aledb_logger import user_extra
from pipeline.util import get_shared_directories, transfer_to_azure
from pipeline.azure_pipeline_util import run_pipeline
from pipeline.azure_upload_util import run_upload_script, get_output_directory_names, download_blobs_from_folder
from pipeline.models import Run, Attempt, get_runs

import logging

logger = logging.getLogger(__name__)


@login_required(login_url='/accounts/login/')
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


@login_required(login_url='/accounts/login/')
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


@login_required(login_url='/accounts/login/')
def pipeline(request):
    context = get_user_context(request.user)
    pipeline_runs = get_runs(request.user)
    context.update({"pipeline_runs": pipeline_runs})

    logger.info("pipeline_manager", extra=user_extra(request))

    if request.method == "POST":
        try:
            template = loader.get_template("pipeline/pipeline_manager.html")
            data_location = request.POST['data_location']
            input_dir = request.POST['folder_name']
            run_name = request.POST['run_name']
            vm_size = request.POST['vm_size']
            xpmd = request.POST['xpmd']
            if len(str(input_dir)) > 5 and len(str(run_name)) > 5:
                run = Run(name=run_name, user=request.user, xpmd=xpmd)
                if data_location == 'drive':
                    context.update({"response_text": request.POST})
                    run.status = "transferring"
                    run.save()
                    transfer_to_azure(input_dir)
                elif data_location == 'azure':
                    run.status = "running"
                    run.save()
                    attempt = Attempt(run=run, vm=vm_size, input=input_dir, output=run_name)
                    attempt.save()
                    run_pipeline(input_dir, run_name, vm_size=vm_size)
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