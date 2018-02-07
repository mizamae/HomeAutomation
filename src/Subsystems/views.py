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

from MainAPP.constants import SUBSYSTEM_HEATING
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
        return render(request, APP_TEMPLATE_NAMESPACE+'/heating.html') 
    else:
        DVs=DevicesAPP.models.Devices.objects.filter(Subsystem__Name=SUBSYSTEM_HEATING)
        for DV in DVs:
            DV.updateAutomationVars()
            
        VARs=MainAPP.models.AutomationVariables.objects.filter(Subsystem__Name=SUBSYSTEM_HEATING)
        VARs_values=[]
        for VAR in VARs:
            data=VAR.getLatestData()[str(VAR.Tag)]
            VARs_values.append([data['timestamp'],data['value']])
        
        SCHs=DevicesAPP.models.MainDeviceVarWeeklySchedules.objects.filter(Subsystem__Name=SUBSYSTEM_HEATING)
        import datetime
        now=datetime.datetime.now()
        from django.contrib.messages import get_messages
        storage = get_messages(request)
        accordion3=False
        for message in storage:
            if 'accordion3' == message.message:
                accordion3=True
            
        return render(request, APP_TEMPLATE_NAMESPACE+'/heating.html',{'DVs':DVs,
                                                                       'VARs':VARs,
                                                                       'VARs_values':VARs_values,
                                                                       'SCHs':SCHs,
                                                                       'DJNGO_HOUR':now.hour,
                                                                       'accordion3':accordion3,
                                                                       }) 

def activateSchedule(request,pk):
    if not checkUserPermissions(request=request,action='activate',model='schedule'):
        return HttpResponseRedirect(reverse(LOGIN_PAGE))
    
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('home'))
    else:
        SCHD=DevicesAPP.models.MainDeviceVarWeeklySchedules.objects.get(pk=pk)
        SCHD.setActive(value=not SCHD.Active)
        messages.info(request, 'accordion3')
        return redirect(request.META['HTTP_REFERER'])

def modifySchedule(request,pk,value,sense):
    import decimal
    if not checkUserPermissions(request=request,action='change',model='schedule'):
        return HttpResponseRedirect(reverse(LOGIN_PAGE))
    
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('home'))
    else:
        SCHD=DevicesAPP.models.MainDeviceVarWeeklySchedules.objects.get(pk=pk)
        SCHD.modify(value=value,sense=sense)
        messages.info(request, 'accordion3')
        return redirect(request.META['HTTP_REFERER'])