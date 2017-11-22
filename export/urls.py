from django.conf.urls import url

from export import views

__author__ = 'dgosting'

urlpatterns = [
    url('^$', views.export, name="export"),
    url('^datapackage/$', views.export_datapackage, name="export_datapackage"),
]
