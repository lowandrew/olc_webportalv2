from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.jobs, name='jobs'),
    url(r'^submit', views.submit, name='submit')
]
