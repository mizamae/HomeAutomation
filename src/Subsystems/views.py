# coding: utf-8

import pandas as pd
import numpy as np
import datetime
import json
import logging
import sys
import pytz
from tzlocal import get_localzone
import itertools

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth import login
from django.core.urlresolvers import reverse
from django.http import HttpResponse,HttpResponseNotFound,HttpResponseRedirect
from django.shortcuts import render, render_to_response,get_object_or_404,redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger("project")

from MainAPP.constants import SUBSYSTEM_HEATING,SUBSYSTEM_GARDEN,SUBSYSTEM_ACCESS
from .constants import APP_TEMPLATE_NAMESPACE

import DevicesAPP.models
import MainAPP.models

LOGIN_PAGE='accounts:login'

def checkUserPermissions(request,action,model):
    # performing some custom type of logic
    if not request.user.has_perm('DevicesAPP.'+action+'_'+model):
        return False
    else:
        return True

def home(request):
    if request.method == 'POST': # the form has been submited
        return render(request, APP_TEMPLATE_NAMESPACE+'/home.html') 
    else:
        return render(request, APP_TEMPLATE_NAMESPACE+'/home.html') 

def heating(request):
    if request.method == 'POST': # the form has been submited
        return render(request, APP_TEMPLATE_NAMESPACE+'/subsystem.html') 
    else:
        DVs=DevicesAPP.models.Devices.objects.filter(Subsystem__Name=SUBSYSTEM_HEATING)
            
        VARs=MainAPP.models.AutomationVariables.objects.filter(Subsystem__Name=SUBSYSTEM_HEATING).exclude(Table='outputs')
        VARs_values=[]
        for VAR in VARs:
            data=VAR.getLatestData()[str(VAR.Tag)]
            VARs_values.append([data['timestamp'],data['value']])
        
        SCHs=DevicesAPP.models.MainDeviceVarWeeklySchedules.objects.filter(Subsystem__Name=SUBSYSTEM_HEATING).order_by('Var','-Active')
        
        GPIOs=DevicesAPP.models.MasterGPIOs.objects.filter(Subsystem__Name=SUBSYSTEM_HEATING)
        
        import datetime
        now=datetime.datetime.now()
        from django.contrib.messages import get_messages
        storage = get_messages(request)
        accordion1=False
        accordion2=True
        accordion3=False
        accordion4=False
        for message in storage:
            if 'accordion1' == message.message:
                accordion1=True # defines if the accordion 1 is initially displayed or collapsed
            elif 'accordion2' == message.message:
                accordion2=True # defines if the accordion 2 is initially displayed or collapsed
            elif 'accordion3' == message.message:
                accordion2=True # defines if the accordion 2 is initially displayed or collapsed
                accordion3=True # defines if the accordion 3 is initially displayed or collapsed
            elif 'accordion4' == message.message:
                accordion4=True # defines if the accordion 4 is initially displayed or collapsed
            
        
        from EventsAPP.models import Events
        EVTs=Events.objects.all()
    
        return render(request, APP_TEMPLATE_NAMESPACE+'/subsystem.html',{'title':MainAPP.models.Subsystems.getName2Display(Name=SUBSYSTEM_HEATING),
                                                                        'DVs':DVs,
                                                                       'VARs':VARs,
                                                                       'VARs_values':VARs_values,
                                                                       'SCHs':SCHs,
                                                                       'DJNGO_HOUR':now.hour,
                                                                       'accordion1':accordion1,
                                                                       'accordion2':accordion2,
                                                                       'accordion3':accordion3,
                                                                       'accordion4':accordion4,
                                                                       'GPIOs':GPIOs,
                                                                       'EVTs':EVTs,
                                                                       }) 

def garden(request):
    if request.method == 'POST': # the form has been submited
        return render(request, APP_TEMPLATE_NAMESPACE+'/subsystem.html') 
    else:
        DVs=DevicesAPP.models.Devices.objects.filter(Subsystem__Name=SUBSYSTEM_GARDEN)
            
        VARs=MainAPP.models.AutomationVariables.objects.filter(Subsystem__Name=SUBSYSTEM_GARDEN).exclude(Table='outputs')
        VARs_values=[]
        for VAR in VARs:
            data=VAR.getLatestData()[str(VAR.Tag)]
            VARs_values.append([data['timestamp'],data['value']])
        
        SCHs=DevicesAPP.models.MainDeviceVarWeeklySchedules.objects.filter(Subsystem__Name=SUBSYSTEM_GARDEN).order_by('Var','-Active')
        
        GPIOs=DevicesAPP.models.MasterGPIOs.objects.filter(Subsystem__Name=SUBSYSTEM_GARDEN)
        
        import datetime
        now=datetime.datetime.now()
        from django.contrib.messages import get_messages
        storage = get_messages(request)
        accordion1=False
        accordion2=True
        accordion3=False
        accordion4=False
        for message in storage:
            if 'accordion1' == message.message:
                accordion1=True # defines if the accordion 1 is initially displayed or collapsed
            elif 'accordion2' == message.message:
                accordion2=True # defines if the accordion 2 is initially displayed or collapsed
            elif 'accordion3' == message.message:
                accordion2=True # defines if the accordion 2 is initially displayed or collapsed
                accordion3=True # defines if the accordion 3 is initially displayed or collapsed
            elif 'accordion4' == message.message:
                accordion4=True # defines if the accordion 4 is initially displayed or collapsed
            
        
        from EventsAPP.models import Events
        EVTs=Events.objects.all()
    
        return render(request, APP_TEMPLATE_NAMESPACE+'/subsystem.html',{'title':MainAPP.models.Subsystems.getName2Display(Name=SUBSYSTEM_GARDEN),
                                                                        'DVs':DVs,
                                                                       'VARs':VARs,
                                                                       'VARs_values':VARs_values,
                                                                       'SCHs':SCHs,
                                                                       'DJNGO_HOUR':now.hour,
                                                                       'accordion1':accordion1,
                                                                       'accordion2':accordion2,
                                                                       'accordion3':accordion3,
                                                                       'accordion4':accordion4,
                                                                       'GPIOs':GPIOs,
                                                                       'EVTs':EVTs,
                                                                       }) 

def access(request):
    if request.method == 'POST': # the form has been submited
        return render(request, APP_TEMPLATE_NAMESPACE+'/subsystem.html') 
    else:
        DVs=DevicesAPP.models.Devices.objects.filter(Subsystem__Name=SUBSYSTEM_ACCESS)
            
        VARs=MainAPP.models.AutomationVariables.objects.filter(Subsystem__Name=SUBSYSTEM_ACCESS).exclude(Table='outputs')
        VARs_values=[]
        for VAR in VARs:
            data=VAR.getLatestData()[str(VAR.Tag)]
            VARs_values.append([data['timestamp'],data['value']])
        
        SCHs=DevicesAPP.models.MainDeviceVarWeeklySchedules.objects.filter(Subsystem__Name=SUBSYSTEM_ACCESS).order_by('Var','-Active')
        
        GPIOs=DevicesAPP.models.MasterGPIOs.objects.filter(Subsystem__Name=SUBSYSTEM_ACCESS)
        
        import datetime
        now=datetime.datetime.now()
        from django.contrib.messages import get_messages
        storage = get_messages(request)
        accordion1=False
        accordion2=True
        accordion3=False
        accordion4=False
        for message in storage:
            if 'accordion1' == message.message:
                accordion1=True # defines if the accordion 1 is initially displayed or collapsed
            elif 'accordion2' == message.message:
                accordion2=True # defines if the accordion 2 is initially displayed or collapsed
            elif 'accordion3' == message.message:
                accordion2=True # defines if the accordion 2 is initially displayed or collapsed
                accordion3=True # defines if the accordion 3 is initially displayed or collapsed
            elif 'accordion4' == message.message:
                accordion4=True # defines if the accordion 4 is initially displayed or collapsed
            
        
        from EventsAPP.models import Events
        EVTs=Events.objects.all()
    
        return render(request, APP_TEMPLATE_NAMESPACE+'/subsystem.html',{'title':MainAPP.models.Subsystems.getName2Display(Name=SUBSYSTEM_ACCESS),
                                                                        'DVs':DVs,
                                                                       'VARs':VARs,
                                                                       'VARs_values':VARs_values,
                                                                       'SCHs':SCHs,
                                                                       'DJNGO_HOUR':now.hour,
                                                                       'accordion1':accordion1,
                                                                       'accordion2':accordion2,
                                                                       'accordion3':accordion3,
                                                                       'accordion4':accordion4,
                                                                       'GPIOs':GPIOs,
                                                                       'EVTs':EVTs,
                                                                       }) 