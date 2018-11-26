from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views

__author__ = 'dgosting'

urlpatterns = [
    url(r'^login/$', views.login_user, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/'}, name='logout'),
]
