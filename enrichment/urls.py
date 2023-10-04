from django.urls import include, re_path

import enrichment.views


urlpatterns = [
    re_path('^$', enrichment.views.enrichment_mutations, name="enrichment")
]
