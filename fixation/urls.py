from django.urls import include, re_path

import fixation.views


urlpatterns = [
    re_path('^$', fixation.views.fixating_mutations, name='fixation')
]
