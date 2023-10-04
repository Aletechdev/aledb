from django.urls import include, re_path

from bibliome import views

urlpatterns = [re_path(r'^$', views.bibliome, name="bibliome")]