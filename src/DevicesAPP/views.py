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

from . import forms
from . import models

from .constants import APP_TEMPLATE_NAMESPACE,LOCAL_CONNECTION,REMOTE_TCP_CONNECTION,MEMORY_CONNECTION, \
                        FORM_FIRST_RENDER_MSG,FORM_ISVALID_MSG,FORM_ISNOTVALID_MSG,SCAN_DEVICENOFOUND,SCAN_DEVICEFOUND,TESTS_USER_AGENT

def home(request):
    if request.method == 'POST': # the form has been submited
        return render(request, APP_TEMPLATE_NAMESPACE+'/home.html') 
    else:
        return render(request, APP_TEMPLATE_NAMESPACE+'/home.html') 

def modelSplitter(model):
    if model=='devices':
        Header1 = models.Devices._meta.verbose_name.title()
        Model=models.Devices
        FormModel=forms.DevicesForm
        FormKwargs={'action':'add+scan'}
        message=models.Devices._meta.verbose_name.title()+ str(_(' saved OK'))
        lastAction='getLabels'
    elif model=='devicetypes':
        Header1 = models.DeviceTypes._meta.verbose_name.title()
        Model=models.DeviceTypes
        FormModel=forms.DeviceTypesForm
        FormKwargs={'action':'add'}
        message=models.DeviceTypes._meta.verbose_name.title()+ str(_(' saved OK'))
        lastAction='add'
    else:
        return HttpResponseNotFound('<h1>No Page Here</h1>') 
    return {'Header1':Header1,'Model':Model,'FormModel':FormModel,'FormKwargs':FormKwargs,'message':message,'lastAction':lastAction}

def checkUserPermissions(request,action,model):
    # performing some custom type of logic
    if not request.user.has_perm('DevicesAPP.'+action+'_'+model):
        return False
    else:
        return True
    
# VIEWS FOR THE MODELS
#@login_required
#@user_passes_test(lambda u: u.has_perm('DevicesAPP.add_devices'))
def add(request,model):
    
    if not checkUserPermissions(request=request,action='add',model=model):
        return HttpResponseRedirect(reverse('accounts:login'))
        
    data=modelSplitter(model=model)
    Header1=str(_('Adding a new ')) +data['Header1']
    Model=data['Model']
    FormModel=data['FormModel']
    FormKwargs=data['FormKwargs']
    message=data['message']
    lastAction=data['lastAction']
    
    if request.method == 'POST': # the form has been submited
        form=FormModel(request.POST,**FormKwargs)
        if form.is_valid():
            instance=form.save()
            if lastAction!='add':
                FormKwargs['action']=lastAction
                ShowForm=True
            else:
                ShowForm=False
            form=FormModel(instance=instance,**FormKwargs)
            
            return render(request, APP_TEMPLATE_NAMESPACE+'/add.html',{'Header1':Header1,
                                                                       'GreenHead':message,
                                                                       'RedMessages':[],
                                                                       'ShowForm':ShowForm,
                                                                       'TestMsg':FORM_ISVALID_MSG,
                                                                       'Form': form
                                                                       })
        else:
            return render(request, APP_TEMPLATE_NAMESPACE+'/add.html',{'Header1':Header1,
                                                                       'GreenMessages':[],
                                                                       'RedMessages':[_('Something is wrong with the data provided'),],
                                                                       'ShowForm':True,
                                                                       'TestMsg':FORM_ISNOTVALID_MSG,
                                                                       'Form': form
                                                                       })
    else:
        form=FormModel(**FormKwargs)
        return render(request, APP_TEMPLATE_NAMESPACE+'/add.html',{'Header1':Header1,
                                                                   'GreenMessages':[],
                                                                   'RedMessages':[],
                                                                   'ShowForm':True,
                                                                   'TestMsg':FORM_FIRST_RENDER_MSG,
                                                                   'Form': form
                                                                   })
    
def setCustomLabels(request,pk):
    Header1=str(_('Setting up the labels for the data from ')) 
    if request.method == 'POST': # the form has been submited
        DV=models.Devices.objects.get(pk=pk)
        DGs=models.Datagrams.objects.filter(DVT=DV.DVT)
        form=forms.DatagramCustomLabelsForm(request.POST,DV=DV,DGs=DGs)
        if form.is_valid():
            CustomLabels=form.get_variablesLabels()
            DV.CustomLabels=json.dumps(CustomLabels)
            DV.save()
            DV.updateAutomationVars()
            message= str(_('Custom labels for device ')) + DV.Name + str(_(' have been set properly.'))
            return render(request, APP_TEMPLATE_NAMESPACE+'/add.html',{'Header1':Header1+ DV.Name,
                                                                   'GreenHead':message,
                                                                   'RedMessages':[],
                                                                   'ShowForm':False,
                                                                   'TestMsg':FORM_ISVALID_MSG,
                                                                   'Form': form
                                                                   })
        else:
            return render(request, APP_TEMPLATE_NAMESPACE+'/add.html',{'Header1':Header1+ DV.Name,
                                                                   'GreenMessages':[],
                                                                   'RedMessages':[],
                                                                   'ShowForm':False,
                                                                   'TestMsg':FORM_ISNOTVALID_MSG,
                                                                   'Form': form
                                                                   })
    else:
        DV=models.Devices.objects.get(pk=pk)
        DGs=models.Datagrams.objects.filter(DVT=DV.DVT)
        form=forms.DatagramCustomLabelsForm(None,DV=DV,DGs=DGs)
        return render(request, APP_TEMPLATE_NAMESPACE+'/add.html',{'Header1':Header1 + DV.Name,
                                                                   'GreenMessages':[],
                                                                   'RedMessages':[],
                                                                   'ShowForm':True,
                                                                   'TestMsg':FORM_FIRST_RENDER_MSG,
                                                                   'Form': form
                                                                   }) 

@user_passes_test(lambda u: u.has_perm('DevicesAPP.scan_devices'))
def scan(request,model):
    data=modelSplitter(model=model)
    Header1=str(_('Scanning for a new ')) +data['Header1']
    Model=data['Model']
    FormModel=data['FormModel']
    message=data['message']
    lastAction=data['lastAction']
    
    if request.method == 'POST': # the form has been submited
        if 'HTTP_USER_AGENT' in request.META and request.META['HTTP_USER_AGENT']==TESTS_USER_AGENT:
            IP='127.0.0.1'
        else:
            IP=None
        IP='127.0.0.1'
        scan=Model.scan(FormModel=FormModel,IP=IP)
        RedMessages=[]
        if scan['devicetype']!=None:
            GreenHead=str(_('Found a ')) + scan['devicetype']
            TestMsg=SCAN_DEVICEFOUND
            ShowForm=True
        else:
            RedMessages.append(_('No device was found'))
            GreenHead=''
            TestMsg=SCAN_DEVICENOFOUND
            ShowForm=False
        if scan['errors']!=[]:
            for error in scan['errors']:
                RedMessages.append(error)
            
        return render(request, APP_TEMPLATE_NAMESPACE+'/add.html',{'Header1':Header1,
                                                                   'GreenHead':GreenHead,
                                                                   'GreenMessages':[],
                                                                   'RedMessages':RedMessages,
                                                                   'ShowForm':ShowForm,
                                                                   'TestMsg':TestMsg,
                                                                   'Form': scan['Form']
                                                                   })
    else:
        form=FormModel(action='scan')
        return render(request, APP_TEMPLATE_NAMESPACE+'/add.html',{'Header1':Header1,
                                                                    'TestMsg':FORM_FIRST_RENDER_MSG,
                                                                   'ShowForm':True,
                                                                   'Form': form}) 
                

def viewList(request,model):
    if not checkUserPermissions(request=request,action='view',model=model):
        return HttpResponseRedirect(reverse('accounts:login'))
    
    data=modelSplitter(model=model)
    Header1=str(_('List of ')) +data['Header1']
    Model=data['Model']
    FormModel=data['FormModel']
    message=data['message']
    lastAction=data['lastAction']
    
    if request.method == 'POST': # the form has been submited
        return HttpResponseNotFound('<h1>No Page Here</h1>') 
    else:
        if Model == models.Devices:
            DVs=Model.objects.all()
            remote_DVs=DVs.filter(DVT__Connection=REMOTE_TCP_CONNECTION)
            numrows_remote=remote_DVs.count()
            local_DVs=DVs.filter(DVT__Connection=LOCAL_CONNECTION)
            numrows_local=local_DVs.count()
            memory_DVs=DVs.filter(DVT__Connection=MEMORY_CONNECTION)
            numrows_memory=memory_DVs.count()
            return render(request, APP_TEMPLATE_NAMESPACE+'/showDevicesList.html',{'numrows_remote':numrows_remote,'RemotedeviceList':remote_DVs,
                                                                            'numrows_local':numrows_local,'LocaldeviceList':local_DVs,
                                                                            'numrows_memory':numrows_memory,'MemorydeviceList':memory_DVs,})
        elif Model == models.DeviceTypes:
            DVTs=Model.objects.all()
            numrows=DVTs.count()
            message_norows=str(_('There are no ')) + data['Header1'] +str(_(' registered.'))
            return render(request, APP_TEMPLATE_NAMESPACE+'/showList.html',{'Header1':Header1,
                                                                            'numrows':numrows,
                                                                            'message_norows':message_norows,
                                                                            'rows':DVTs
                                                                            })

def edit(request,model,pk):
    if not checkUserPermissions(request=request,action='change',model=model):
        return HttpResponseRedirect(reverse('accounts:login'))
    
    data=modelSplitter(model=model)
    Header1=str(_('Editing a ')) +data['Header1']
    Model=data['Model']
    FormModel=data['FormModel']
    message=data['message']
    lastAction=data['lastAction']
    
    Instance = get_object_or_404(Model, pk=pk)
    
    if request.method == 'POST': # the form has been submited
        form=FormModel(request.POST,action='edit',instance=Instance)
        #form.setUser(user=request.user)
        if form.is_valid():
            form.save()
            return render(request, APP_TEMPLATE_NAMESPACE+'/add.html',{'Message':' saved OK','Form':None}) 
        else:
            return render(request, APP_TEMPLATE_NAMESPACE+'/add.html',{'Form':form}) 
    else:
        form=FormModel(action='edit',instance=Instance)
        return render(request, APP_TEMPLATE_NAMESPACE+'/add.html',{'Status':'Initial','Form': form}) 

@login_required
@user_passes_test(lambda u: u.has_perm('DevicesAPP.view_devices'))
def AdvancedDevicePage(request,pk):
    DV=models.Devices.objects.get(pk=pk)
    LatestData=DV.getLatestData()
    return render(request, APP_TEMPLATE_NAMESPACE + '/'+DV.DVT.Code+'.html',
                                                        {'Device':DV,'Latest':LatestData})
# END

@csrf_exempt
def asynchronous_datagram(request):
    import xml.etree.ElementTree as ET
    from utils.BBDD import getRegistersDBInstance
    from .models import Devices,Datagrams
    if request.method == 'POST':
        DB=getRegistersDBInstance()
        xmltext=str(request.body,'utf-8').replace("'","")
        root = ET.fromstring(xmltext)
        (result,datagram)=Devices.parseDatagram(xmlroot=root)
        logger.info('Async Request: Datagram ' + str(datagram))
        if result==0:
            timestamp=timezone.now()  
            deviceCode=datagram[0]
            datagramCode=datagram[1]
            DV=Devices.objects.get(Code=deviceCode)
            DG=Datagrams.objects.get(DVT=DV.DVT,Code=int(datagramCode))
            del datagram[0:2]
            if DV!=None and DG!=None:
                DV.insertRegister(TimeStamp=timestamp, DatagramId=DG.Identifier, year=timestamp.year, values=datagram)

        else:
            print('The datagram received was not properly formatted: ' + datagram)
        
    else: #GET
        logger.info('Asynchronous Request with GET format. No longer supported.')

    return HttpResponse(status=204) #The server successfully processed the request and is not returning any content

@login_required
def ajax_get_data_for_devicetype(request,devicetypePK):
    if request.is_ajax():
        DVT=models.DeviceTypes.objects.get(pk=devicetypePK)
        info={'Connection':DVT.Connection}
        return HttpResponse(json.dumps(info))
    else:
        return HttpResponse(json.dumps([]))

@login_required
def ajax_get_orders_for_device(request,devicePK):
    if request.is_ajax():
        DV=models.Devices.objects.get(pk=devicePK)
        orders=models.DeviceCommands.objects.filter(DVT=DV.DVT)
        info=[]
        if len(orders)>0:
            for order in orders:
                info.append({'Identifier':order.Identifier,'HumanTag':order.HumanTag})
                
        return HttpResponse(json.dumps(info))
    else:
        return HttpResponse(json.dumps([]))
    