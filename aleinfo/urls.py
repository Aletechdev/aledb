from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, re_path
from django.conf import settings
from django.contrib import admin
from aleinfo.views import protected_file_serve


# TODO: remove all final '/' for apps that don't need it (enrichment, converge, fixed need because of shared app.)
urlpatterns = [
    re_path(r'^', include('home.urls')),
    re_path(r'^dashboard', include('dashboard.urls')),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^admin/defender/', include('defender.urls')),  # defender admin
    re_path(r'^accounts/', include('accounts.urls', namespace="accounts")),
    # re_path(r'^accounts/', include('django.contrib.auth.urls')),
    re_path(r'^about', include('about.urls')),
    re_path(r'^ale/', include('ale.urls')),
    re_path(r'^bibliome/', include('bibliome.urls')),
    re_path(r'^converge/', include('converge.urls')),
    re_path(r'^enrichment/', include('enrichment.urls')),
    re_path(r'^evidence/', include('evidence.urls')),
    re_path(r'^export', include('export.urls')),
    re_path(r'^home', include('home.urls')),
    re_path(r'^md_export', include('md_export.urls')),
    re_path(r'^filter/', include('filter.urls')),
    re_path(r'^fixation/', include('fixation.urls')),
    re_path(r'^metadata/', include('metadata.urls')),
    re_path(r'^mutations/', include('seq.urls')),
    re_path(r'^pipeline', include('pipeline.urls')),
    re_path(r'^goggles', include('goggles.urls')),
    re_path(r'^search/', include('search.urls')),
    re_path(r'^stats/', include('stats.urls')),
    re_path(r'^aledata/(?P<page_name>.*)$', protected_file_serve)
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ] + staticfiles_urlpatterns()
