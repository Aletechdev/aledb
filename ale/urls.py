from django.conf.urls import url
from ale.views import FilteredProjectListView, FilteredExperimentListView, project_detail, experiment_detail

urlpatterns = [
    url(r'^projects/', FilteredProjectListView.as_view(), name="projects_view"),
    url(r'^experiments/', FilteredExperimentListView.as_view(), name="experiments_view"),
    url(r"^project/(?P<pk>[0-9]+)/$", project_detail, name="project_detail"),
    url(r"^experiment/(?P<pk>[0-9]+)/$", experiment_detail, name="experiment_detail"),
]