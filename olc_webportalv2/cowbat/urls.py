from olc_webportalv2.cowbat import views
from django.conf.urls import url, include

urlpatterns = [
    url(r'^$', views.cowbat_home, name='cowbat_home'),
    url(r'^cowbat_processing/(?P<sequencing_run_pk>\d+)/$', views.cowbat_processing, name='cowbat_processing'),
    url(r'^download_run/(?P<run_folder>\d{6}_[A-Z]+)/$', views.download_run_info, name='download_run_info'),
]
