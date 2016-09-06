from django.conf.urls import url

from compare.views import index, mutation_table, enrichment_table

__author__ = 'dgosting'


urlpatterns = [
    url(r'^$', index.compare, name='compare'),
    url(r'^mutations', mutation_table.compared_mutations, name='compared_mutations')
]
