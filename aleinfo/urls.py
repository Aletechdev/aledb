from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.conf.urls import include, url

import django.contrib.auth.views


urlpatterns = [url(r'^accounts/login/$', django.contrib.auth.views.login),
               url(r'^', include('seq.urls')),
               url(r'^filter', include('filter.urls')),
               url(r'^fixation', include('fixation.urls')),
               url(r'^stats', include('stats.urls')),
               url(r'^metadata', include('metadata.urls')),
               url(r'^enrichment', include('enrichment.urls'))
               ]

urlpatterns += staticfiles_urlpatterns()
