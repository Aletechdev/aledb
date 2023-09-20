from django.urls import include, re_path

from genes import views

__author__ = 'dgosting'

urlpatterns = [
    re_path('^$', views.gene, name="gene"),
]
