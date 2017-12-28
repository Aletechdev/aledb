from django.conf.urls import url
from combine.views import index, mutation_table, enrichment, metadata, fixation


__author__ = 'dgosting'


urlpatterns = [
    url(r'^$', index.combine, name='combine'),
    url(r'^mutations', mutation_table.combined_mutations, name='combined_mutations'),
    url(r'^metadata', metadata.combined_metadata, name='combined_metadata'),
    url(r'^enrichment', enrichment.combined_enrichment_mutations, name='combined_enrichment_mutations'),
    url(r'^fixation', fixation.combined_fixation, name='combined_fixation'),
]
