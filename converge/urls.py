from django.urls import include, re_path

import converge.views


urlpatterns = [
    re_path('^$', converge.views.converge_mutations, name="converge")
]
