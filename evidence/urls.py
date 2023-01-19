from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.evidence, name='evidence'),
    url(r'^(?P<value>\d+)/$', views.evidence, name='evidence_location'),
]