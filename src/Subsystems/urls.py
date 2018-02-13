# coding: utf-8
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^home/$',views.home, name='home'),
    url(r'^heating/$',views.heating, name='heating'),
    ]

