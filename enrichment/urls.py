from django.conf.urls import patterns, url

import enrichment.views

urlpatterns = patterns('',
                       url('^$', enrichment.views.enrichment_mutations, name="enrichment"),
                       url('^shared', enrichment.views.shared_enrichment_mutations, name="shared_enrichment_mutations")
                       )
