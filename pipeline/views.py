# Create your views here.
import subprocess
from datetime import datetime, timezone
from django.http import HttpResponse
from django.shortcuts import redirect

from common.util import get_user_context

from django.template import loader
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from logs.aledb_logger import user_extra
from pipeline.util import get_shared_directories, transfer_to_azure
from pipeline.azure_pipeline_util import run_pipeline
from pipeline.azure_upload_util import run_upload_script, get_output_directory_names, download_blobs_from_folder
from pipeline.azure_batch_status_util import get_task_list, get_log_file
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
def upload(request, name):
    logger.info("uploading {} via webapp".format(name), extra=user_extra(request))
    try:
        run = Run.objects.get(name=name)
        run.status = "uploading"
        run.save()
        upload_cmd = ['ssh', '-i', '/root/.ssh/aledb', 'root@aledb.org', '/upload/webapp-upload.sh {}'.format(name)]
        subprocess.Popen(upload_cmd)
        run.status = "done"
        run.save()
        return redirect(pipeline)
    except Exception:
        logger.exception("webapp upload broke", extra=user_extra(request))


@login_required(login_url='/accounts/login/')
def pipeline(request):
    logger.info("pipeline_manager", extra=user_extra(request))
    context = get_user_context(request.user)
    pipeline_runs = get_runs(request.user)
    context.update({"pipeline_runs": pipeline_runs})
    try:
        if request.method == "POST":
            try:
                template = loader.get_template("pipeline/pipeline_manager.html")
                data_location = request.POST['data_location']
                input_dir = request.POST['folder_name'].strip().strip('/')
                run_name = request.POST['run_name']
                vm_size = request.POST['vm_size']
                xpmd = request.POST['xpmd']
                if len(str(input_dir)) > 5 and len(str(run_name)) > 5:
                    run, created = Run.objects.get_or_create(name=run_name, user=request.user, xpmd=xpmd)
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
    except Exception as e:
        logger.exception(e, extra = user_extra(request))


@staff_member_required(login_url='/accounts/login/')
def log(request, job, task):
    return HttpResponse(get_log_file(job, task), content_type='text/plain')


@login_required(login_url='/accounts/login/')
def run(request, id):
    try:
        context = get_user_context(request.user)
        current_run = Run.objects.get(id=id)
        task_list = get_task_list(current_run.name)
        run_details = []
        complete_count = 0
        for task in task_list:
            if task.state.value == "running":
                current_time = datetime.now(timezone.utc)
                duration = current_time - task.execution_info.start_time
            elif task.execution_info.end_time:
                duration = task.execution_info.end_time - task.execution_info.start_time
                complete_count = complete_count+1
            else:
                duration = "N/A"
            task_detail = (task, duration)
            run_details.append(task_detail)
        context.update({"run_details": run_details, "current_run": current_run, "complete_count": complete_count})
        logger.info("run_details", extra=user_extra(request))

        if request.method == "POST":
            context.update({"response_text": request.POST})
            try:
                template = loader.get_template("pipeline/run.html")
                download_blobs_from_folder(request.POST['azure_output_folder'])

                return HttpResponse(template.render(context, request), content_type="text/html")
            except Exception:
                logger.exception("webapp upload broke", extra=user_extra(request))
        try:
            template = loader.get_template("pipeline/run.html")

            return HttpResponse(template.render(context, request), content_type="text/html")
        except Exception:
            logger.exception("webapp upload broke", extra=user_extra(request))
    except Exception as e:
        logger.exception(e, extra = user_extra(request))
    return None
