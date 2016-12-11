from django.conf.urls import url

import seq.views.mutations
import seq.views.common_mutations
import seq.views.search
import seq.views.gene
import seq.views.duplication


# TODO: Understand if '-' is better than "_" within a URL.
urlpatterns = [
    url('^mutations$', seq.views.mutations.mutation_table, name="mutation_table"),
    url('^common_mutations', seq.views.common_mutations.common_mutations, name="common_mutations"),
    url('^search', seq.views.search.search, name="search"),
    url('^gene', seq.views.gene.gene, name="gene"),
    url('^duplication', seq.views.duplication.duplication, name="duplication"),
]
