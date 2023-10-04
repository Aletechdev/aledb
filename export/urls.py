from django.urls import include, re_path

from export import views

__author__ = 'dgosting'

urlpatterns = [
    re_path('^$', views.export, name="export"),
]
