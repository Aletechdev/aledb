from django.shortcuts import get_object_or_404, render
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django.shortcuts import redirect
from django.views.generic import DetailView, CreateView
from .filters import AleExperimentFilter, ProjectFilter
from .models import Project, AleExperiment
from .tables import ProjectTable, ExperimentTable


def projects(request):
    project_list = Project.objects.all()
    table = ProjectTable(project_list)
    return render(request, 'ale/projects.html', {'table': table})


class FilteredProjectListView(SingleTableMixin, FilterView):
    table_class = ProjectTable
    model = Project
    template_name = "ale/projects.html"
    filterset_class = ProjectFilter

    def get_queryset(self):
        return super(FilteredProjectListView, self).get_queryset()

    def get_table_kwargs(self):
        return {"template_name": "django_tables2/bootstrap.html"}


class FilteredExperimentListView(SingleTableMixin, FilterView):
    table_class = ExperimentTable
    model = AleExperiment
    template_name = "ale/experiments.html"
    filterset_class = AleExperimentFilter

    def get_queryset(self):
        return super(FilteredExperimentListView, self).get_queryset()

    def get_table_kwargs(self):
        return {"template_name": "django_tables2/bootstrap.html"}


def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)

    # hide the project column, as it is not very interesting for a list of experiments for a project.
    table = ExperimentTable(project.aleexperiment_set.all(),)
    return render(request, "ale/project_detail.html", {"project": project, "table": table})


def experiment_detail(request, pk):
    # experiment = get_object_or_404(AleExperiment, pk=pk)
    # context = {
    #     "ale_experiment_id": experiment.ale_id,
    #     "ale_experiment_name": experiment.name,
    # }
    url = "/stats?ale_experiment_id="+pk
    return redirect(url)


class ExperimentDetailView(DetailView):
    queryset = AleExperiment.objects.all()


class ProjectCreateView(CreateView):
    model = Project
    fields = ('name', 'discription', 'user', 'status', 'is_public')

