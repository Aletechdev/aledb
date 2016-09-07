from django.conf.urls import url

from compare.views import index, mutation_table, enrichment, metadata, fixation

__author__ = 'dgosting'


urlpatterns = [
    url(r'^$', index.compare, name='compare'),
    url(r'^mutations', mutation_table.compared_mutations, name='compared_mutations'),
    url(r'^metadata', metadata.comparison_metadata, name='compared_metadata'),
    url(r'^enrichment', enrichment.compared_enrichment_mutations, name='compared_enrichment_mutations'),
    url(r'^fixation', fixation.comparison_fixation, name='compared_fixation'),
]
