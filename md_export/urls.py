from django.conf.urls import url
from md_export import views

urlpatterns = [
    url('^$', views.md_export, name="md_export"),
]
