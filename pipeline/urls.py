from django.urls import include, re_path

from pipeline import views

__author__ = 'Patrick Phaneuf'

urlpatterns = [
    re_path('^$', views.pipeline, name="pipeline"),
]
