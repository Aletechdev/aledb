from django.urls import include, re_path

from goggles import views

from .consumers import GraphConsumer

urlpatterns = [
    re_path('^$', views.goggles, name="goggles"),
    re_path(r'^alegoggles/graph/', GraphConsumer.connect, name="ws"),

]
