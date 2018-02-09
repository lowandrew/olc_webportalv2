from django.conf.urls import url
from . import views


urlpatterns = [

    # Index page
    url(r'^$', views.multisampleprojects, name='multisampleprojects'),

]
