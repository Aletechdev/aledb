from django.urls import include, re_path

from about import views

__author__ = 'Patrick Phaneuf'

urlpatterns = [
    re_path('^$', views.about, name="about"),
]
