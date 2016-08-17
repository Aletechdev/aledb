from django.conf.urls import url

from . import views

from filter.global_filter import global_filter


urlpatterns = [
    url(r'^$', views.mutation_filter, name='filter'),
    url(r'^global_filter', global_filter, name='global_filter'),
]
