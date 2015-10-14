from django.conf.urls import patterns, url

from seq.views import index
from seq.views import mutations
from seq.views import experiments
from seq.views import key_mutations
from seq.views import select_lineage


urlpatterns = patterns('',
                       url('^$', index.index, name="index"),
                       url('^mutations$', mutations.mutation_table, name="mutation_table"),
                       url('^key_mutations$', key_mutations.key_mutations, name="key_mutations"),
                       url('^lists$', experiments.lists, name="lists"),
                       url('^select_lineage', select_lineage.select_lineage, name="select_lineage"),
                       )
