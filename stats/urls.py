from django.urls import include, re_path

from . import views

__author__ = 'dgosting'


urlpatterns = [
    re_path(r'^$', views.stats, name='stats'),
]
