from django.conf.urls import include, url#, patterns
from django.conf import settings


# TODO: remove all final '/' for apps that don't need it (enrichment, etc.)
urlpatterns = [
    url(r'^', include('dashboard.urls')),
    url(r'^accounts/login/', include('login.urls')),
    url(r'^mutations', include('seq.urls')),
    url(r'^filter/', include('filter.urls')),
    url(r'^fixation/', include('fixation.urls')),
    url(r'^stats', include('stats.urls')),
    url(r'^metadata', include('metadata.urls')),
    url(r'^about', include('about.urls')),
    url(r'^enrichment/', include('enrichment.urls')),
    url(r'^export', include('export.urls')),
    url(r'^compare/', include('compare.urls')),
    url(r'^search/', include('search.urls')),
    url(r'^duplication/', include('duplications.urls')),
    url(r'^gene/', include('genes.urls')),
    url(r'^common_mutations/', include('commmonmuts.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
else:
    urlpatterns += patterns('', (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}))
