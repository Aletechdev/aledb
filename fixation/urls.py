from django.conf.urls import url

import fixation.views


urlpatterns = [
    url('^$', fixation.views.fixating_mutations, name='fixation')
]
