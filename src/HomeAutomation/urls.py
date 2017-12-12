# coding: utf-8
"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
import Master_GPIOs.views
import Devices.GlobalVars
import accounts.urls
import profiles.urls

from . import views

import logging

logger = logging.getLogger("project")      

urlpatterns = [
    url(r'^$', views.HomePageDevice.as_view(), name='home'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    #url(r'^$', views.HomePage.as_view(), name='home'),
    url(r'^about/$', views.AboutPage.as_view(), name='about'),
    url(r'^adddevice/$', login_required(views.AddDevice.as_view()), name='adddevice'),
    url(r'^reqconf/(\d{1,3})/$', views.ConfDevice, name='reqconf'),
    url(r'^showdevlist/$', views.ShowDeviceList, name='devlist'),
    url(r'^togglestate/(?P<devicename>.+)/$', views.ToggleDevice, name='togglestate'),
    url(r'^deletedev/(?P<devicename>.+)/$', views.DeleteDevice, name='delDevice'),
    url(r'^repbuilder/(?P<number>.+)/$', views.reportbuilder, name='repbuilder'),
    url(r'^ajax_get_orders_for_device/(?P<devicePK>.+)/$', views.ajax_get_orders_for_device, name='ajax_get_orders_for_device'),
    url(r'^ajax_get_data_for_devicetype/(?P<devicetypePK>.+)/$', views.ajax_get_data_for_devicetype, name='ajax_get_data_for_devicetype'),
    url(r'^async_post/$', views.asynchronous_datagram, name='asynchronous_datagram'),
    url(r'^devicepage/(?P<pk>.+)/$', views.AdvancedDevicepage, name='devicepage'),
    url(r'^charts/$', views.device_report,name='devicecharts'),
    url(r'^settimezone/$', views.settimezone,name='settimezone'),
    url(r'^advancedDevice/$', views.AdvancedDevice.as_view(),name='advancedDevice'),
    url(r'^advancedDevice/arduinoCode/$', views.arduinoCode,name='arduinoCode'),
    url(r'^master_gpios/$', Master_GPIOs.views.master_gpios,name='master_gpios'),
    url(r'^reports/$', views.viewReports,name='viewReports'),
    url(r'^reports/(?P<pk>.+)/$', views.viewReports,name='viewReports'),
    url(r'^reportpreview/(?P<title>.+)/$', views.previewReport,name='previewReport'),
    url(r'^owntracks/(?P<user>.+)/$', views.handleLocation,name='handleLocation'),
    url(r'^userubication/$', views.viewUserUbication,name='viewUserUbication'),
    url(r'^view_schedules/$', views.viewSchedules,name='viewSchedules'),
    url(r'^activateSchedule/(?P<pk>.+)/$', views.activateSchedule,name='activateSchedule'),
    url(r'^modifySchedule/(?P<pk>.+)/(?P<value>.+)/(?P<sense>.+)/$', views.modifySchedule,name='modifySchedule'),
    url(r'^view_rules/$', views.viewRules,name='viewRules'),
    url(r'^activateRule/(?P<pk>.+)/$', views.activateRule,name='activateRule'),
    url(r'^gitupdate/$', views.GitUpdate,name='gitupdate'),
    url(r'^softreset/$', views.SoftReset,name='softreset'),
    url(r'^users/', include(profiles.urls, namespace='profiles')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/Devices/setcustomlabels/(?P<devicePK>.+)/$',views.adminSetCustomLabels,name='adminSetCustomLabels'),
    url(r'^admin/RemoteDevices/setcustomlabels/(?P<connection>.+)/(?P<devicePK>.+)/$',views.adminSetCustomLabels,name='adminSetCustomLabels'),
    url(r'^admin/LocalDevices/setcustomlabels/(?P<connection>.+)/(?P<devicePK>.+)/$',views.adminSetCustomLabels,name='adminSetCustomLabels'),
    
    url(r'^', include(accounts.urls, namespace='accounts')),
    
]

handler500 = 'HomeAutomation.views.custom_error500_view'

# User-uploaded files like profile pics need to be served in development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Include django debug toolbar if DEBUG is on
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
