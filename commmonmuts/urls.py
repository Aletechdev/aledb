from django.conf.urls import url

from commmonmuts import views

__author__ = 'dgosting'

urlpatterns = [
    url('^$', views.common_mutations, name="common_mutations"),
]
