from django.urls import include, re_path, path

from pipeline import views

__author__ = 'Muyao'

urlpatterns = [
    path('', views.pipeline, name="pipeline"),
    path('upload/<str:name>', views.upload, name='upload'),
    path('drive/', views.drive, name='drive'),
    path('run/<int:id>', views.run, name='run'),
    path('run/log/<str:job>/<str:task>', views.log, name='log'),
]
