from django.conf.urls import url

import converge.views

urlpatterns = [
    url('^$', converge.views.converge_mutations, name="converge"),
]
