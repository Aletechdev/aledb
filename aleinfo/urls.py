from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.conf.urls import include, url

import django.contrib.auth.views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = [url(r'^accounts/login/$', django.contrib.auth.views.login),

               # Uncomment the admin/doc line below to enable admin documentation:
               url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

               # Uncomment the next line to enable the admin:
               url(r'^admin/', include(admin.site.urls)),  # TODO: remove if we're not using the Django site admin functionality.

               url(r'^ale_analytics/', include('seq.urls')),
               url(r'^ale_analytics/filter/', include('filter.urls')),
               url(r'^ale_analytics/fixation/', include('fixation.urls')),
               url(r'^ale_analytics/stats/', include('stats.urls')),
               url(r'^ale_analytics/meta_data/', include('metadata.urls')),
               url(r'^ale_analytics/freq_mutated_genes/', include('hot_gene_mutations.urls'))
               ]

urlpatterns += staticfiles_urlpatterns()
