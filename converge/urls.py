from django.conf.urls import url

import converge.views


urlpatterns = [
    url('^$', converge.views.converge_mutations, name="converge"),
    url('^shared', converge.views.shared_converge_genes, name="shared_converge_mutations")
]
