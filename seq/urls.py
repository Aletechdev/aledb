from django.conf.urls import patterns, url

import seq.views.index
import seq.views.mutations
import seq.views.common_mutations
import seq.views.meta_data
import seq.views.search
import seq.views.gene
import seq.views.duplication
import seq.views.dashboard


# TODO: Understand if '-' is better than "_" within a URL.
urlpatterns = patterns('',
                       url('^$', seq.views.index.index, name="index"),
                       url('^mutations$', seq.views.mutations.mutation_table, name="mutation_table"),
                       url('^common_mutations', seq.views.common_mutations.common_mutations, name="common_mutations"),
                       url('^meta_data', seq.views.meta_data.meta_data, name="meta_data"),
                       url('^search', seq.views.search.search, name="search"),
                       url('^gene', seq.views.gene.gene, name="gene"),
                       url('^duplication', seq.views.duplication.duplication, name="duplication"),
                       url('^dashboard', seq.views.dashboard.dashboard, name="dashboard")
                       )
