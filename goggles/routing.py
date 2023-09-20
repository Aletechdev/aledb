from django.urls import include, re_path

from .consumers import GraphConsumer

urlpatterns = [
    re_path(r'^alegoggles/graph/', GraphConsumer, name="goggles"),
]
