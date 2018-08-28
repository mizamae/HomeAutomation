# coding: utf-8
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^home/$',views.home, name='home'),
    url(r'^(?P<system>.+)/$',views.generic, name='generic'),
    ]

