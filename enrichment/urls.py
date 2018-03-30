from django.conf.urls import url

import enrichment.views


urlpatterns = [
    url('^$', enrichment.views.enrichment_mutations, name="enrichment")
]
