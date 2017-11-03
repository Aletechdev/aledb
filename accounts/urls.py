from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views

from . import views

__author__ = 'dgosting'

urlpatterns = [
    url(r'^login/$', views.login_user, name='login'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    url(r'^admin/', admin.site.urls),
]
