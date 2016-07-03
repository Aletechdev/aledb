from django.conf.urls import patterns, url

import seq.views.index
import seq.views.mutations
import seq.views.experiments
import seq.views.key_mutated_genes
import seq.views.key_mutations
import seq.views.select_lineage
import seq.views.lineage
import seq.views.meta_data
import seq.views.search
import seq.views.filter
import seq.views.gene
import seq.views.duplication
import seq.views.dashboard


# TODO: Understand if '-' is better than "_" within a URL.
urlpatterns = patterns('',
                       url('^$', seq.views.index.index, name="index"),
                       url('^mutations$', seq.views.mutations.mutation_table, name="mutation_table"),
                       url('^key_mutated_genes$', seq.views.key_mutated_genes.key_mutated_genes, name="key_mutated_genes"),
                       url('^lists$', seq.views.experiments.lists, name="lists"),
                       url('^select_lineage', seq.views.select_lineage.select_lineage, name="select_lineage"),
                       url('^lineage', seq.views.lineage.lineage, name="lineage"),
                       url('^meta_data', seq.views.meta_data.meta_data, name="lineage"),
                       url('^search', seq.views.search.search, name="search"),
                       url('^filter', seq.views.filter.create_filter, name="filter"),
                       url('^gene', seq.views.gene.gene, name="gene"),
                       url('^duplication', seq.views.duplication.duplication, name="duplication"),
                       url('^dashboard', seq.views.dashboard.dashboard, name="dashboard")
                       )
