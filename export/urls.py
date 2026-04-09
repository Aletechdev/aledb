from django.urls import include, re_path

from export import views

__author__ = 'dgosting'

urlpatterns = [
    re_path('^$', views.export, name="export"),
    re_path('^/experiment_index$', views.export_experiment_index, name="export_experiment_index"),
]
