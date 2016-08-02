from django.conf.urls import url

import hot_gene_mutations.views

urlpatterns = [url('^$', hot_gene_mutations.views.hot_gene_mutations, name="hot_gene_mutations"),
               url('^shared', hot_gene_mutations.views.shared_hot_gene_mutations, name="shared_hot_gene_mutations")
               ]
