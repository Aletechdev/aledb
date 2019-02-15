from django.shortcuts import get_object_or_404, render
from django.shortcuts import redirect
from .models import Project, AleExperiment
from .utils import get_user_projects, get_all_user_exps
from .permissions import can_view_project
from logs.aledb_logger import user_extra
import logging

logger = logging.getLogger(__name__)


def projects(request):
    project_list = get_user_projects(request.user)
    template_name = "ale/projects.html"
    return render(request, template_name, {'projects': project_list})


def experiments(request):
    experiment_list = get_all_user_exps(request.user)
    template_name = "ale/experiments.html"
    return render(request, template_name, {'experiments': experiment_list})


def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if can_view_project(request.user, project):
        experiments = project.aleexperiment_set.all()
        return render(request, "ale/project_detail.html", {"project": project, "experiments": experiments})
    return render(request, "403.html")


def experiment_detail(request, pk):
    # experiment = get_object_or_404(AleExperiment, pk=pk)
    # context = {
    #     "ale_experiment_id": experiment.ale_id,
    #     "ale_experiment_name": experiment.name,
    # }
    url = "/stats?ale_experiment_id="+pk
    return redirect(url)



