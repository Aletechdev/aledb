from django.urls import include, re_path
from ale.views import projects, experiments, project_detail, experiment_detail

urlpatterns = [
    re_path(r'^projects', projects, name="projects_view"),
    re_path(r'^experiments', experiments, name="experiments_view"),
    re_path(r"^project/(?P<pk>[0-9]+)/$", project_detail, name="project_detail"),
    re_path(r"^experiment/(?P<pk>[0-9]+)/$", experiment_detail, name="experiment_detail"),
]