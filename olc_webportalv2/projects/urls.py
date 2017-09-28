from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.projects, name='projects'),
    url(r'^project/(?P<project_id>\d+)/$', views.project_detail, name="project_detail")
]
