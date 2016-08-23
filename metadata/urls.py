from django.conf.urls import url

from . import views

__author__ = 'dgosting'

urlpatterns = [
    url('^$', views.metadata, name="meta_data"),
]
