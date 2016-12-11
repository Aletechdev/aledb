from django.conf.urls import url

from metadata import views

__author__ = 'dgosting'

urlpatterns = [
    url('^$', views.metadata, name="metadata"),
]
