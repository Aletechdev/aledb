from django.conf.urls import patterns, url

from seq import views

urlpatterns = patterns('',
    url('^$', views.index, name="index"),
    url('^lists$', views.lists, name="lists"),
    url('^experiments$', views.experiment_table, name="experiment_table"),
    url('^mutations$', views.mutation_table, name="mutation_table"),
    url('^isolates$', views.isolate_list, name="isolate_table"),
    url('^lineage$', views.lineage_table, name="lineage_table"),
    url('^summary$', views.mutation_summary, name="mutation_summary")
)
