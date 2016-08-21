from django.conf.urls import url

from filter.views import ale_exp_filter
from filter.views import global_filter

urlpatterns = [
    url(r'^$', ale_exp_filter.mutation_filter, name='filter'),
    url(r'^global_filter', global_filter.global_filter, name='global_filter'),
]
