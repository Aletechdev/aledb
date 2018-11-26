from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import include, url
from django.conf import settings
from django.contrib import admin


# TODO: remove all final '/' for apps that don't need it (enrichment, converge, fixed need because of shared app.)
urlpatterns = [
    url(r'^', include('dashboard.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('accounts.urls', namespace="accounts")),
    # url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^mutations', include('seq.urls')),
    url(r'^filter/', include('filter.urls')),
    url(r'^fixation/', include('fixation.urls')),
    url(r'^stats', include('stats.urls')),
    url(r'^metadata', include('metadata.urls')),
    url(r'^about', include('about.urls')),
    url(r'^enrichment/', include('enrichment.urls')),
    url(r'^converge/', include('converge.urls')),
    url(r'^export', include('export.urls')),
    url(r'^combine/', include('combine.urls')),
    url(r'^search/', include('search.urls')),
    url(r'^bibliome/', include('bibliome.urls')),
    url(r'^gene/', include('genes.urls'))
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + staticfiles_urlpatterns()
