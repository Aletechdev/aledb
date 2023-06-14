from django.conf.urls import url

from pipeline import views

__author__ = 'Patrick Phaneuf'

urlpatterns = [
    url('^$', views.pipeline, name="pipeline"),
]
