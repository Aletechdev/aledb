from django.conf.urls import url

from duplications import views

__author__ = 'dgosting'

urlpatterns = [
    url('^$', views.duplication, name="duplication"),
]
