from django.conf.urls import patterns, url

import seq.views.index
import seq.views.mutations
import seq.views.experiments
import seq.views.key_mutations
import seq.views.select_lineage
import seq.views.lineage
import seq.views.meta_data
import seq.views.search


urlpatterns = patterns('',
                       url('^$', seq.views.index.index, name="index"),
                       url('^mutations$', seq.views.mutations.mutation_table, name="mutation_table"),
                       url('^key_mutations$', seq.views.key_mutations.key_mutations, name="key_mutations"),
                       url('^lists$', seq.views.experiments.lists, name="lists"),
                       url('^select_lineage', seq.views.select_lineage.select_lineage, name="select_lineage"),
                       url('^lineage', seq.views.lineage.lineage, name="lineage"),
                       url('^meta_data', seq.views.meta_data.meta_data, name="lineage"),
                       url('^search_form', seq.views.search.search_form, name="search_form"),
                       url('^search_view', seq.views.search.search, name="search_view"),
                       )
