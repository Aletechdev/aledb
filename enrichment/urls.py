from django.conf.urls import url

import enrichment.views

urlpatterns = [
    url('^$', enrichment.views.enrichment_mutations, name="enrichment"),
    url('^shared', enrichment.views.shared_enrichment_mutations, name="shared_enrichment_mutations")
]
