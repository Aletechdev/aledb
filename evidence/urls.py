from django.conf.urls import url

import evidence.views

urlpatterns = [
    url('^$', evidence.views, name="evidence")
]
