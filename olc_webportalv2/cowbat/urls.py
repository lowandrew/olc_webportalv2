from olc_webportalv2.cowbat import views
from django.conf.urls import url, include

urlpatterns = [
    url(r'^$', views.cowbat_home, name='cowbat_home'),
    url(r'^cowbat_processing$', views.cowbat_processing, name='cowbat_processing'),
]
