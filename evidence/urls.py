from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.evidence, name='evidence'),
]