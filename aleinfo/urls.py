from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.conf.urls import include, url


# TODO: remove all final '/' for apps that don't need it (enrichment, etc.)
urlpatterns = [
    url(r'^', include('dashboard.urls')),
    url(r'^accounts/login/', include('login.urls')),
    url(r'^mutations', include('seq.urls')),
    url(r'^filter/', include('filter.urls')),
    url(r'^fixation/', include('fixation.urls')),
    url(r'^stats', include('stats.urls')),
    url(r'^metadata', include('metadata.urls')),
    url(r'^enrichment/', include('enrichment.urls')),
    url(r'^export', include('export.urls')),
    url(r'^compare/', include('compare.urls')),
    url(r'^search/', include('search.urls')),
    url(r'^duplication/', include('duplications.urls')),
    url(r'^gene/', include('genes.urls')),
]

urlpatterns += staticfiles_urlpatterns()
