from django.urls import include, re_path

from search import views

__author__ = 'dgosting'

urlpatterns = [
    re_path('^$', views.search, name="search"),
]
