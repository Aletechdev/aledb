from django.conf.urls import url

from . import views

__author__ = 'dgosting'

urlpatterns = [
    url('^$', views.meta_data, name="meta_data"),
]
