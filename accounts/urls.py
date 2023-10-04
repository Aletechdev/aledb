from django.urls import include, re_path
from django.contrib.auth import views as auth_views

app_name = 'accounts'

urlpatterns = [
    re_path(r'^login/$', auth_views.LoginView.as_view(), name='login'),
    re_path(r'^logout/$', auth_views.LogoutView.as_view(), {'next_page': '/'}, name='logout'),
]
