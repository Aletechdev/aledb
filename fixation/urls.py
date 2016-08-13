from django.conf.urls import url

import fixation.views


urlpatterns = [
    url('^$', fixation.views.fixating_mutations, name='fixation'),
    url('^shared', fixation.views.shared_fixating_mutations, name='shared_fixating_mutations'),
]
