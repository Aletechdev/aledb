from django.urls import include, re_path

from goggles import views

from .consumers import GogglesConsumer

urlpatterns = [
    re_path('^$', views.goggles, name="goggles"),
    re_path(r'^alegoggles/graph/', GogglesConsumer.connect, name="ws"),

]
