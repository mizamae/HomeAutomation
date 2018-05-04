# coding: utf-8
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^home/$',views.home, name='home'),
    
    # DEVICES AND DEVICETYPES MODELS
    url(r'^add/(?P<model>.+)/$',views.add, name='add'),
    url(r'^setcustomlabels/(?P<pk>.+)/$',views.setCustomLabels, name='setCustomLabels'),
    url(r'^scan/(?P<model>.+)/$',views.scan, name='scan'),
    url(r'^view_all/(?P<model>.+)/$',views.viewList, name='view_all'),
    url(r'^modify/(?P<model>.+)/(?P<pk>.+)/$',views.edit, name='edit'),
    url(r'^toggle/(?P<model>.+)/(?P<pk>.+)/$',views.toggle, name='toggle'),
    url(r'^graph/(?P<model>.+)/$',views.viewGraphs, name='graph'),
    url(r'^advanceddevicepage/(?P<pk>.+)/$',views.AdvancedDevicePage, name='devicepage'),
    url(r'^async_post/$', views.asynchronous_datagram, name='asynchronous_datagram'),
    url(r'^ajax_get_orders_for_device/(?P<devicePK>.+)/$', views.ajax_get_orders_for_device, name='ajax_get_orders_for_device'),
    url(r'^ajax_get_data_for_devicetype/(?P<devicetypePK>.+)/$', views.ajax_get_data_for_devicetype, name='ajax_get_data_for_devicetype'),
    ]

