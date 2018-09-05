# coding: utf-8
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from django.utils import timezone
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
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.http import Http404 
from django.http import HttpResponse
from django.shortcuts import render, render_to_response,get_object_or_404,redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers

import utils.BBDD

from .constants import REGISTERS_DB_PATH,GIT_PATH

from EventsAPP.consumers import PublishEvent
from . import models
from . import forms
import MainAPP.forms


logger = logging.getLogger("project")
LOGIN_PAGE='accounts:login'

def modelSplitter(model):
    if model=='automationvars':
        Header1 = models.AutomationVariables._meta.verbose_name.title()
        Model=models.AutomationVariables
        FormModel=None
        FormKwargs={}
        message=models.AutomationVariables._meta.verbose_name.title()+ str(_(' saved OK'))
        lastAction='add'
    elif model=='automationvarweeklyschedule':
        Header1 = models.AutomationVarWeeklySchedules._meta.verbose_name.title()
        Model=models.AutomationVarWeeklySchedules
        FormModel=None
        FormKwargs={}
        message=models.AutomationVarWeeklySchedules._meta.verbose_name.title()+ str(_(' saved OK'))
        lastAction='add'
    else:
        return None
    return {'Header1':Header1,'Model':Model,'FormModel':FormModel,'FormKwargs':FormKwargs,'message':message,'lastAction':lastAction}

def checkUserPermissions(request,action,model):
    # performing some custom type of logic
    if not request.user.has_perm('MainAPP.'+action+'_'+model):
        return False
    else:
        return True

def activateSchedule(request,pk):
    if not checkUserPermissions(request=request,action='activate',model='maindevicevarweeklyschedules'):
        return HttpResponseRedirect(reverse(LOGIN_PAGE))
    
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('home'))
    else:
        
        SCHD=models.AutomationVarWeeklySchedules.objects.get(pk=pk)
        SCHD.setActive(value=not SCHD.Active)
        messages.info(request, 'accordion3')
        return redirect(request.META['HTTP_REFERER'])

def modifySchedule(request,pk,value,sense):
    import decimal
    if not checkUserPermissions(request=request,action='change',model='maindevicevarweeklyschedules'):
        return HttpResponseRedirect(reverse(LOGIN_PAGE))
    
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('home'))
    else:
        SCHD=models.AutomationVarWeeklySchedules.objects.get(pk=pk)
        SCHD.modify(value=value,sense=sense)
        messages.info(request, 'accordion3')
        return redirect(request.META['HTTP_REFERER'])
    
def toggle(request,model,pk):
    if not checkUserPermissions(request=request,action='toggle',model=model):
        return HttpResponseRedirect(reverse(LOGIN_PAGE))
    
    data=modelSplitter(model=model)
    Model=data['Model']
    Instance = get_object_or_404(Model, pk=pk)
    
    if request.method == 'GET':
        if model=='automationvars':
            Instance.toggle()
            messages.info(request, 'accordion2')
        else:
            return HttpResponseNotFound('<h1>No Page Here for Model '+str(model)+'</h1>') 
        
    return redirect(request.META['HTTP_REFERER'])

# def test(request):
#       
#     if request.method == 'GET':
#         from .tasks import checkCustomCalculations
#         checkCustomCalculations()
#         return HttpResponseNotFound('<h1>No Page Here for Model '+str(model)+'</h1>') 
#           
#     return redirect(request.META['HTTP_REFERER'])


class Home(generic.TemplateView):
    template_name = "home.html"

class AboutPage(generic.TemplateView):
    template_name = "about.html"

@user_passes_test(lambda u: u.is_superuser)
def SiteSettings(request):
    if not checkUserPermissions(request=request,action='change',model='SiteSettings'):
        return HttpResponseRedirect(reverse(LOGIN_PAGE))
    SETTINGS=models.SiteSettings.load()
    if request.method == 'POST':
        
        form=forms.SiteSettingsForm(request.POST,instance=SETTINGS)
        redmessages=[]
        greenmessages=[]
        
        if form.is_valid() and form.has_changed():
            instance=form.save()
            greenmessages.append(_('Changes updated OK'))
        elif not form.is_valid():
            redmessages.append(_('Something is wrong with the data provided'))
        return render(request, 'sitesettings.html', {'Form': form,
                                                     'GreenMessages':greenmessages,
                                                     'RedMessages':redmessages,
                                                     'CurrentValues':serializers.serialize("json",models.SiteSettings.objects.all())}
                      )
    else:
        form=forms.SiteSettingsForm(initial=SETTINGS.__dict__,instance=SETTINGS)
        return render(request, 'sitesettings.html', {'Form': form,
                                                     'GreenMessages':[],
                                                     'RedMessages':[],
                                                     'CurrentValues':serializers.serialize("json",models.SiteSettings.objects.all())}
                      )
        
@user_passes_test(lambda u: u.is_superuser)
def settimezone(request):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        PublishEvent(Severity=0,Text=_("Timezone has been set to ") + request.POST['timezone'],Persistent=True,Code='MainAPPViews-Timezone1')
        return HttpResponseRedirect(reverse('configuration'))
    else:
        return render(request, 'timezones.html', {'timezones': pytz.common_timezones})
        

@user_passes_test(lambda u: u.is_superuser)
def configuration(request):
    from EventsAPP.models import Events
    EVTs=Events.objects.all()
    from utils.GoogleDrive import GoogleDriveWrapper
    instance=GoogleDriveWrapper()
    BackupActive=instance.checkCredentials()
    return render(request, 'configuration.html',{'EVTs':EVTs,'BackupActive':BackupActive})

@login_required
@user_passes_test(lambda u: u.has_perm('profiles.view_tracking'))
def viewUserUbication(request):
    if request.method == 'POST':
        pass
    else:
        from authtools.models import User
        users = User.objects.all()
        for usr in users:
            if usr.profile.tracking:
                pass
        return render(request, 'trackUsers.html',{'Users':users})

@login_required
def thermostats(request):
    THERMs=models.Thermostats.objects.all()
    return render(request, 'thermostats.html',{'THERMs':THERMs})

@csrf_exempt
def handleLocation(request,user):
    #print('Received request for location ' +request.method+' ' +str(request.body))
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        #print('JSON: ' + str(request.body.decode('utf-8')))
        from authtools.models import User
        users = User.objects.all()
        #print('Looking for user : ' + str(user))
        for usr in users:
            #print('Checked user : ' + str(usr))
            if usr.email.find(user)>=0:
                #print('Found user : ' + str(usr))
                if usr.profile.tracking:
                    usr.profile.updateLocationData(Latitude=data['lat'],Longitude=data['lon'],Accuracy=data['acc'])
                    # usr.profile.Latitude=data['lat']
                    # usr.profile.Longitude=data['lon']
                    # usr.profile.Accuracy=data['acc']
                    # usr.profile.LastUpdated=timestamp
                    # usr.profile.save()
                    
        #JSON: {"_type":"location","tid":"MZ","acc":54,"batt":79,"conn":"m","lat":42.8175305,"lon":-1.6015541,"t":"u","tst":1510664016}
        
        # tid: identification of the user
        # acc: Accuracy of the reported location in meters
        # conn: connection type, m for mobile, w for wifi, o for offline
        return HttpResponse(status=204) #The server successfully processed the request and is not returning any content
                
@user_passes_test(lambda u: u.is_superuser)
def arduinoCode(request):
    import Devices.Arduino_generator
    import os
    import zipfile
    import io
    logger.info('Generating Arduino source files.')
    generated_files=Devices.Arduino_generator.create_arduino_code()
    zip_filename = "Arduino_templates.zip"
    # Open BytesIO to grab in-memory ZIP contents
    s = io.BytesIO()
    # The zip compressor
    zf = zipfile.ZipFile(s, "w")
    for fpath in generated_files:
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)
        zip_subdir = fname.replace('.ino','')
        zip_path = os.path.join(zip_subdir, fname)
        # Add file, at correct path
        zf.write(os.path.join(settings.MEDIA_ROOT,fpath), zip_path)
    # Must close zip for all contents to be written
    zf.close()
    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = HttpResponse(s.getvalue(), content_type = "application/x-zip-compressed")
    # ..and correct content-disposition
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

    return resp

def gdrive_authentication(request):
    from utils.GoogleDrive import GoogleDriveWrapper
    try:
        code=request.GET['code']
    except:
        code=None
    
    if code!=None:
        instance=GoogleDriveWrapper()
        instance.gauth.Auth(code=code)
        instance.saveCredentials()
        
        autenticated=instance.checkCredentials()
        if autenticated:
            PublishEvent(Severity=0,Text=_("Google Drive credentials have been stored"),Persistent=True,Code='MainAPPViews-Drive1')
    else:
        PublishEvent(Severity=4,Text=_("Google Drive permissions were not granted"),Persistent=True,Code='MainAPPViews-Drive1')
    return redirect(reverse('configuration'))

def Notifications(request):
    if request.method == 'POST': # the form has been submited
        data = json.loads(request.body)
        user=request.user
        firstSubscription=user.profile.subscription_token==""
        
        if user.profile.notifications:
            user.profile.set_subscriptionToken(token=data)

        if firstSubscription:
            from utils.web_notifications import NotificationManager
            NotificationManager.send_web_push(users=[user,], title='DIY4dot0 - New subscription', tag='notifications-subscription',
                          message_body="Se han activado las notificaciones para " + str(user),url='http://mizamae2.ddns.net:8075')
        return HttpResponse(status=204) #The server successfully processed the request and is not returning any content
    else:
        return HttpResponseNotFound() 
    
@user_passes_test(lambda u: u.is_superuser)
def DBBackup(request):
    from utils.GoogleDrive import GoogleDriveWrapper
    instance=GoogleDriveWrapper()
    
    if request.method == 'POST':
        pass
    else:
        autenticated=instance.checkCredentials()
        if autenticated:
            instance.deleteCredentials()
            #instance.uploadDBs()
            PublishEvent(Severity=0,Text=_("Google Drive credentials have been deleted"),Persistent=True,Code='MainAPPViews-Drive1')
            pass
        else:
            return redirect(instance.AUTH_URL)
    return redirect(reverse('configuration'))

@user_passes_test(lambda u: u.is_superuser)
def SoftReset(request):
    import os
    os.system("sudo systemctl restart gunicorn")
    PublishEvent(Severity=0,Text=_("Gunicorn processes restarted"),Persistent=False,Code='MainAPPViews-0')
    id='Restarting-daphne worker'
    from utils.asynchronous_tasks import BackgroundTimer
    Timer=BackgroundTimer(interval=15,threadName=id,callable=os.system,kwargs={'command':"sudo systemctl restart daphne worker"})
    return HttpResponse(status=204) #The server successfully processed the request and is not returning any content
    
@user_passes_test(lambda u: u.is_superuser)
def GitUpdate(request):
    from os import walk
    for root, dirs, n in walk(GIT_PATH):
        if ".git" in dirs:
            from utils.GitHub import update
            revision=update(root)
            from utils.web_notifications import NotificationManager
            timestamp=timezone.now()
            NotificationManager.send_web_push(users=NotificationManager.getUsers(), title='DIY4dot0',timestamp=timestamp, tag='notifications-gitupdate',
                          message_body="Se ha actualizado las version al codigo " + revision,url='http://mizamae2.ddns.net:8075')
            if revision!=None:
                SETTINGS=models.SiteSettings.load()
                SETTINGS.VERSION_CODE=revision
                SETTINGS.save(update_fields=['VERSION_CODE',])
            break
    return HttpResponse(status=204) #The server successfully processed the request and is not returning any content

def custom_error500_view(request):
    exceptionType= sys.exc_info()[0].__name__
    if exceptionType=='XMLException':
        exceptionDescription='FAILURE IN THE CONFIGURATION XML FILE: ' +str(sys.exc_info()[1])
    else:
        exceptionDescription='Internal server error. No more information provided for security reasons. \n' +'  - '+str(sys.exc_info()[1])
    return render(request,'500.html',{'exception_value': exceptionDescription})
