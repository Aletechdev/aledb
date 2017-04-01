from django.conf.urls import url

from genes import views

__author__ = 'dgosting'

urlpatterns = [
    url('^$', views.gene, name="gene"),
]
