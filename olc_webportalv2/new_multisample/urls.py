from . import views
from django.conf.urls import url


urlpatterns = [

    # Index page
    url(r'^$', views.new_multisample, name='new_multisample'),
    # Individual project page
    url(r'^project/(?P<project_id>\d+)/$',
        views.project_detail, name="project_detail"),

    # Upload data for project
    url(r'^project/(?P<project_id>\d+)/upload$',
        views.upload_samples, name="upload_samples"),
]
