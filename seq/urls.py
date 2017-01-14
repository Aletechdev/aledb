from django.conf.urls import url

import seq.views.mutations
import seq.views.common_mutations


# TODO: Understand if '-' is better than "_" within a URL.
urlpatterns = [
    url(r'^$', seq.views.mutations.mutation_table, name="mutation_table"),
    url('^common_mutations', seq.views.common_mutations.common_mutations, name="common_mutations"),
]
