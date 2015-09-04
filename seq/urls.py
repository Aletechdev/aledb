from django.conf.urls import patterns, url

from seq.views import index
from seq.views import mutation_tables
from seq.views import experiment_tables


urlpatterns = patterns('',
                       url('^$', index.index, name="index"),
                       url('^mutations$', mutation_tables.mutation_table, name="mutation_table"),
                       url('^lists$', experiment_tables.lists, name="lists"),
                       )
