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

import utils.BBDD

from .constants import REGISTERS_DB_PATH,GIT_PATH

from Events.consumers import PublishEvent
import MainAPP.models
import MainAPP.forms


logger = logging.getLogger("project")
LOGIN_PAGE='accounts:login'

def modelSplitter(model):
    if model=='automationvars':
        Header1 = MainAPP.models.AutomationVariables._meta.verbose_name.title()
        Model=MainAPP.models.AutomationVariables
        FormModel=None
        FormKwargs={}
        message=MainAPP.models.AutomationVariables._meta.verbose_name.title()+ str(_(' saved OK'))
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


class Home(generic.TemplateView):
    template_name = "home.html"

class AboutPage(generic.TemplateView):
    template_name = "about.html"

@user_passes_test(lambda u: u.is_superuser)
def settimezone(request):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return HttpResponseRedirect(reverse('advancedDevice'))
    else:
        return render(request, 'timezones.html', {'timezones': pytz.common_timezones})

@user_passes_test(lambda u: u.has_perm('HomeAutomation.view_rules'))
def viewRules(request):
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('home'))
    else:
        RULs=HomeAutomation.models.AutomationRuleModel.objects.all().order_by('-Active')
                
        return render(request,'rulesList.html',
                          {'RULs':RULs})   
        
@user_passes_test(lambda u: u.has_perm('HomeAutomation.activate_rule'))
def activateRule(request,pk):
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('home'))
    else:
        RUL=HomeAutomation.models.AutomationRuleModel.objects.get(pk=pk)
        RUL.Active=not RUL.Active
        RUL.save()
        return HttpResponseRedirect(reverse('viewRules'))
        

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
    
@csrf_exempt
def handleLocation(request,user):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        #logger.info('JSON: ' + str(request.body.decode('utf-8')))
        from authtools.models import User
        users = User.objects.all()
        for usr in users:
            if usr.email.find(user)>=0:
                #print('Found user : ' + str(usr))
                if usr.profile.tracking:
                    timestamp=timezone.now()
                    applicationDBs=DevicesAPP.BBDD.DIY4dot0_Databases(registerDBPath=REGISTERS_DB_PATH)
                    applicationDBs.insert_track(TimeStamp=timestamp,User=str(usr.email),Latitude=data['lat'],Longitude=data['lon'],Accuracy=data['acc'])
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
    #raise Http404

@user_passes_test(lambda u: u.is_superuser)
def SoftReset(request):
    import os
    os.system("sudo systemctl restart gunicorn")
    PublishEvent(Severity=0,Text=_("Gunicorn processes restarted"),Persistent=False)
    return HttpResponse(status=204) #The server successfully processed the request and is not returning any content
    
@user_passes_test(lambda u: u.is_superuser)
def GitUpdate(request):
    from os import walk
    for root, dirs, n in walk(GIT_PATH):
        if ".git" in dirs:
            #print("\"%s\" has git dir: \"%s\"" % (root, dirs))
            #dirs.remove('.git')

            update(root)
            break
    return HttpResponse(status=204) #The server successfully processed the request and is not returning any content

def update(root):
    """
    Updates the program via git pull.
    """
    import re    
    from sys import stdout as sys_stdout
    from subprocess import Popen, PIPE
    PublishEvent(Severity=0,Text=_("Checking for updates..."),Persistent=False)

    process = Popen("git pull", cwd=root, shell=True,
                    stdout=PIPE, stderr=PIPE,universal_newlines=True)
    stdout, stderr = process.communicate()
    success = not process.returncode

    if success:
        updated = "Already" not in stdout
        process = Popen("git rev-parse --verify HEAD", cwd=root, shell=True,
                        stdout=PIPE, stderr=PIPE,universal_newlines=True)
        stdout, err = process.communicate()
        revision = (stdout[:7] if stdout and
                    re.search(r"(?i)[0-9a-f]{32}", stdout) else "-")
        PublishEvent(Severity=0,Text=_("%s the latest source revision '%s'.") %
              (_("Already at") if not updated else _("Updated to"), revision),Persistent=False)
        
        if updated:
            # CHECK IF THERE IS ANY UNAPPLIED MIGRATION
            process = Popen("python src/manage.py showmigrations --list", cwd=root, shell=True,
                        stdout=PIPE, stderr=PIPE,universal_newlines=True)
            stdout, err = process.communicate()
            if err:
                logger.debug('MIGRATIONS CHECK ERROR: ' + str(err))
                PublishEvent(Severity=5,Text=_("Error checking migrations: " + str(err)),Persistent=True)
                
            migrations= "[ ]" in stdout
             
            if migrations:
                logger.debug('MIGRATIONS: ' + str(stdout))
                PublishEvent(Severity=0,Text=_("Updating DB with new migrations. Relax, it may take a while"),Persistent=False)
                process = Popen("python src/manage.py migrate", cwd=root, shell=True,
                        stdout=PIPE, stderr=PIPE,universal_newlines=True)
                stdout, err = process.communicate()
                if not err:
                    PublishEvent(Severity=0,Text=_("Django DB updated OK"),Persistent=False)
                else:
                    PublishEvent(Severity=4,Text=_("Error applying the migration: " + str(err)),Persistent=False)
                    logger.debug('MIGRATIONS APPLICATION ERROR: ' + str(err))
                    return
                        
            PublishEvent(Severity=0,Text=_("Restart processes to apply the new changes"),Persistent=False)
    else:
        PublishEvent(Severity=2,Text=_("Problem occurred while updating program."),Persistent=False)
        
        err = re.search(r"(?P<error>error:[^:]*files\swould\sbe\soverwritten"
                      r"\sby\smerge:(?:\n\t[^\n]+)*)", stderr)
        if err:
            def question():
                """Asks question until a valid answer of y or n is provided."""
                print("\nWould you like to overwrite your changes and set "
                      "your local copy to the latest commit?")
                sys_stdout.write("ALL of your local changes will be deleted"
                                 " [Y/n]: ")
                ans = raw_input()

                if not ans:
                    ans = "y"

                if ans.lower() == "n":
                    return False
                elif ans.lower() == "y":
                    return True
                else:
                    #print("Did not understand your answer! Try again.")
                    question()

            #print("%s" % err.group("error"))

            # if not question():
                # return

            if "untracked" in stderr:
                cmd = "git clean -df"
            else:
                cmd = "git reset --hard"

            process = Popen(cmd, cwd=root, shell=True,
                            stdout=PIPE, stderr=PIPE,universal_newlines=True)
            stdout, err = process.communicate()

            if "HEAD is now at" in stdout:
                #print("\nLocal copy reset to current git branch.")
                #print("Attemping to run update again...\n")
                PublishEvent(Severity=0,Text=_("Attemping to run update again..."),Persistent=False)
            else:
                #print("Unable to reset local copy to current git branch.")
                PublishEvent(Severity=5,Text=_("Unable to reset local copy to current git branch."),Persistent=False)
                return

            update(root)
        else:
            #print("Please make sure that you have a 'git' package installed.")
            PublishEvent(Severity=5,Text=_("Please make sure that you have a 'git' package installed. Error: ") + str(stderr),Persistent=False)
            #print(stderr)
            
def custom_error500_view(request):
    exceptionType= sys.exc_info()[0].__name__
    if exceptionType=='XMLException':
        exceptionDescription='FAILURE IN THE CONFIGURATION XML FILE: ' +str(sys.exc_info()[1])
    else:
        exceptionDescription='Internal server error. No more information provided for security reasons. \n' +'  - '+str(sys.exc_info()[1])
    return render(request,'500.html',{'exception_value': exceptionDescription})
