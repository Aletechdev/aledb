from django.conf.urls import url

from search import views

__author__ = 'dgosting'

urlpatterns = [
    url('^$', views.search, name="search"),
]
