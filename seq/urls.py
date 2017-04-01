from django.conf.urls import url

import seq.views.mutations


# TODO: Understand if '-' is better than "_" within a URL.
urlpatterns = [
    url(r'^$', seq.views.mutations.mutation_table, name="mutation_table"),
]
