from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.conf.urls import include, url
from django.conf import settings

urlpatterns = [
    url(r'^accounts/login/', include('login.urls')),
    url(r'^seq/', include('seq.urls')),
    url(r'^', include('dashboard.urls')),
    url(r'^filter/', include('filter.urls')),
    url(r'^fixation/', include('fixation.urls')),
    url(r'^stats', include('stats.urls')),
    url(r'^metadata', include('metadata.urls')),
    url(r'^enrichment/', include('enrichment.urls')),
    url(r'^export', include('export.urls')),
    url(r'^compare/', include('compare.urls')),
]

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
