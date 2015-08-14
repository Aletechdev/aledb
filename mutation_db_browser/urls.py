from django.conf.urls import patterns, url

from mutation_db_browser import views

urlpatterns = patterns('',
                       url('^$', views.mutations_db_browser, name="mutation_db_browser")
                       )
