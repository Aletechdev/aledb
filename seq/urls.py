from django.conf.urls import url

import seq.views.mutations


# TODO: Understand if '-' is better than "_" within a URL.
urlpatterns = [
    url(r'^$', seq.views.mutations.mutation_table, name="mutation_table"),
    url(r'^amplifications', seq.views.mutations.amplification_data, name="amplifications"),
    url(r'^add_to_global_filter', seq.views.mutations.add_to_global_filter, name='mutation_to_global_filter'),
    url(r'^add_to_exp_filter', seq.views.mutations.add_to_exp_filter, name='mutation_to_exp_filter'),
    url(r'^toggle-mut-tag/', seq.views.mutations.save_mut_tag, name='toggle_mut_tag'),
    url(r'^toggle-rep-tag', seq.views.mutations.save_rep_tag, name='toggle_rep_tag'),
]
