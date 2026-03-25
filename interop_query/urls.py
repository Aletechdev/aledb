from django.urls import include, re_path

from interop_query import views

__author__ = 'dgosting'

urlpatterns = [
    re_path(r'^query-by-gene/?$', views.query_by_gene, name='query_by_gene'),
    re_path(r'^query-by-strain/?$', views.query_by_strain, name='query_by_strain'),
    re_path(r'^query-by-pair/?$', views.query_by_pair, name='query_by_pair'),
    re_path(r'^genes/?$', views.genes, name='genes'),
    re_path(r'^strains/?$', views.strains, name='strains'),
    re_path(r'^gene-strain-pairs/?$', views.gene_strain_pairs, name='gene_strain_pairs'),
]