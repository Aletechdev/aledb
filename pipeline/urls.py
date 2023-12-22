from django.urls import include, re_path, path

from pipeline import views

__author__ = 'Muyao'

urlpatterns = [
    path('', views.pipeline, name="pipeline"),
    path('upload/', views.upload, name='upload'),
    path('drive/', views.drive, name='drive'),
    path('manager/', views.manager, name='manager')

]
