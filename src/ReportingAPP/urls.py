# coding: utf-8
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^home/$',views.home, name='home'),
    
    # REPORTS AND REPORTITEMS MODELS
    url(r'^add/(?P<model>.+)/$',views.add, name='add'),
    url(r'^view_all/(?P<model>.+)/$',views.viewList, name='view_all'),
    url(r'^view/(?P<model>.+)/(?P<pk>.+)/$',views.view, name='view'),
    url(r'^preview/(?P<title>.+)/$',views.preview, name='preview'),
    url(r'^delete/(?P<model>.+)/(?P<pk>.+)/$',views.delete, name='delete'),
    url(r'^modify/(?P<model>.+)/(?P<pk>.+)/$',views.edit, name='edit'),
    ]