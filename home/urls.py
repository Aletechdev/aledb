from django.conf.urls import url

from home import views

__author__ = 'Muyao'

urlpatterns = [
    url('^$', views.home, name="home"),
]
