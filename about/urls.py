from django.conf.urls import url

from about import views

__author__ = 'Patrick Phaneuf'

urlpatterns = [
    url('^$', views.about, name="about"),
]
