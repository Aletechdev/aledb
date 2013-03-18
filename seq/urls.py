from django.conf.urls import patterns, url

from seq import views

urlpatterns = patterns('',
    url('^$', views.index, name="index"),
    url('^experiments$', views.experiment_table, name="experiment_table"),
    url('^mutations$', views.mutation_table, name="mutation_table"),
)
