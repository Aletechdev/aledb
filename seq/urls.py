from django.conf.urls import patterns, url

from seq.views import index
from seq.views import mutation_tables
from seq.views import experiment_tables
# from seq.views import views


urlpatterns = patterns('',
                       url('^$', index.index, name="index"),
                       url('^mutations$', mutation_tables.mutation_table, name="mutation_table"),
                       url('^lists$', experiment_tables.lists, name="lists"),
                       # url('^experiments$', views.views.experiment_table, name="experiment_table"),
                       # url('^isolates$', views.views.isolate_list, name="isolate_table"),
                       # url('^lineage$', views.views.lineage_table, name="lineage_table"),
                       # url('^summary$', views.views.mutation_summary, name="mutation_summary")
                       )
