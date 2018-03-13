from . import views
from django.conf.urls import url, include


urlpatterns = [

    # Index page
    url(r'^$', views.new_multisample, name='new_multisample'),
    # Individual project page
    url(r'^project/(?P<project_id>\d+)/$',
        views.project_detail, name="project_detail"),

    # Upload data for project
    url(r'^project/(?P<project_id>\d+)/upload$',
        views.upload_samples, name="upload_samples"),

    url(r'^sample/(?P<sample_id>\d+)/$',
        views.sample_detail, name="sample_detail"),

    url(r'^sample/(?P<sample_id>\d+)/sendsketch_results_table$',
        views.sendsketch_results_table, name="sendsketch_results_table"),

    # GeneSippr result tables.
    url(r'^project/(?P<project_id>\d+)/genesippr_results$',
        views.display_genesippr_results, name="display_genesippr_results"),

    # Confindr result tables.
    url(r'^project/(?P<project_id>\d+)/confindr_results$',
        views.confindr_results_table, name="confindr_results_table"),

    # Remove project
    url(r'^project/(?P<project_id>\d+)/remove$',
        views.project_remove, name="project_remove"),

    # Project remove confirm
    url(r'^project/(?P<project_id>\d+)/remove_confirm$',
        views.project_remove_confirm, name="project_remove_confirm"),

    # Remove sample
    url(r'^sample/(?P<sample_id>\d+)/remove$',
        views.sample_remove, name="sample_remove"),

    # Sample remove confirm
    url(r'^sample/(?P<sample_id>\d+)/remove_confirm$',
        views.sample_remove_confirm, name="sample_remove_confirm"),
]
