from django.conf.urls import patterns, url

import key_mutations.views

urlpatterns = patterns('',
                       url('^$', key_mutations.views.key_mutations, name="key_mutations")
                       )
