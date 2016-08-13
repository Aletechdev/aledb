from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.conf.urls import patterns, include, url


urlpatterns = patterns('',

                       (r'^accounts/login/$', 'django.contrib.auth.views.login'),

                       url(r'^ale_analytics/', include('seq.urls')),
                       url(r'^ale_analytics/filter/', include('filter.urls')),
                       url(r'^ale_analytics/fixation/', include('fixation.urls')),
                       url(r'^ale_analytics/stats/', include('stats.urls')),
                       url(r'^ale_analytics/metadata/', include('metadata.urls')),
                       url(r'^ale_analytics/enrichment/', include('enrichment.urls'))
                       )

urlpatterns += staticfiles_urlpatterns()
