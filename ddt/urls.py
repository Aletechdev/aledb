from django.conf.urls import patterns, url
                                      
from ddt import views


urlpatterns = patterns('',                                                      
                       url(r'^$', views.ddt),
                       )   
