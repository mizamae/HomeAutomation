# coding: utf-8
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^home/$',views.home, name='home'),
    url(r'^heating/$',views.heating, name='heating'),
    url(r'^activateSchedule/(?P<pk>.+)/$', views.activateSchedule,name='activateSchedule'),
    url(r'^modifySchedule/(?P<pk>.+)/(?P<value>.+)/(?P<sense>.+)/$', views.modifySchedule,name='modifySchedule'),
    ]

