from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.projects, name='projects'),

    url(r'^project/(?P<project_id>\d+)/$',
        views.project_detail, name="project_detail"),

    # Tables for the views.project_detail page
    url(r'^project/(?P<project_id>\d+)/project_table$',
        views.project_table, name="project_table"),

    url(r'^project/(?P<project_id>\d+)/genesippr_results_table$',
        views.genesippr_results_table, name="genesippr_results_table"),
]
