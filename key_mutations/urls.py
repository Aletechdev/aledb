from django.conf.urls import patterns, url

import key_mutations.views

urlpatterns = patterns('',
                       url('^$', key_mutations.views.key_mutations, name="key_mutations"),
                       url('^shared', key_mutations.views.shared_key_mutations, name="shared_key_mutations")
                       )
