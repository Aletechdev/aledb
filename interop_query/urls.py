from django.urls import include, re_path

from interop_query import views

__author__ = 'dgosting'

urlpatterns = [
    re_path(r'^gene/?$', views.query_by_gene, name='query_by_gene'),
    re_path(r'^strain/?$', views.query_by_strain, name='query_by_strain'),
    re_path(r'^pair/?$', views.query_by_pair, name='query_by_pair'),
]