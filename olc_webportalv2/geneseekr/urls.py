from olc_webportalv2.geneseekr import views
from django.conf.urls import url, include

urlpatterns = [
    url(r'^geneseekr_home/', views.geneseekr_home, name='geneseekr_home'),
    url(r'^geneseekr_query/', views.geneseekr_query, name='geneseekr_query'),
    url(r'^geneseekr_processing/(?P<geneseekr_request_pk>\d+)/$', views.geneseekr_processing, name='geneseekr_processing'),
    url(r'^geneseekr_results/(?P<geneseekr_request_pk>\d+)/$', views.geneseekr_results, name='geneseekr_results'),
]
