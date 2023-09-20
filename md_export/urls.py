from django.urls import include, re_path
from md_export import views

urlpatterns = [
    re_path('^$', views.md_export, name="md_export"),
]
