__author__ = 'dgosting'

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.lists, name='lists'),
]
