from django.conf.urls import patterns, url

from seq.views import index
from seq.views import mutations
from seq.views import experiments
from seq.views import views
from seq.views import key_mutations


urlpatterns = patterns('',
                       url('^$', index.index, name="index"),
                       url('^mutations$', mutations.mutation_table, name="mutation_table"),
                       url('^key_mutations$', key_mutations.key_mutations, name="key_mutations"),
                       url('^lists$', experiments.lists, name="lists"),
                       url('^lineage$', views.lineage_table, name="lineage_table"),
                       url('^summary$', views.mutation_summary, name="mutation_summary")
                       )
