from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',

                       (r'^accounts/login/$', 'django.contrib.auth.views.login'),

                       # url(r'^grappelli/', include('grappelli.urls')),

                       # Uncomment the admin/doc line below to enable admin documentation:
                       url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

                       # Uncomment the next line to enable the admin:
                       url(r'^admin/', include(admin.site.urls)),   # TODO: remove if we're not using the Django site admin functionality.

                       url(r'^ale_analytics/', include('seq.urls')),
                       url(r'^ale_analytics/filter/', include('filter.urls')),
                       url(r'^ale_analytics/fixation/', include('fixation.urls')),
                       url(r'^ale_analytics/stats/', include('stats.urls')),
                       )

urlpatterns += staticfiles_urlpatterns()
