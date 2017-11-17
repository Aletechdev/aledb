from django.conf.urls import url

from bibliome import views

urlpatterns = [url(r'^$', views.bibliome, name="bibliome")]