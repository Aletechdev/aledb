from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.mutation_filter, name='filter'),
    url(r'^global_filter', views.global_filter, name='global_filter'),
]
