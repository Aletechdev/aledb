from django.conf.urls import url

from export import views

__author__ = 'dgosting'

urlpatterns = [
    url('^$', views.export, name="export"),
]
