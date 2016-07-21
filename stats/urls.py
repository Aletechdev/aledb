from django.conf.urls import url

from . import views

__author__ = 'dgosting'


urlpatterns = [
    url(r'^$', views.stats, name='stats'),
]
