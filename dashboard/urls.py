from django.urls import include, re_path

from dashboard import views

urlpatterns = [re_path(r'^$', views.dashboard, name="dashboard")]