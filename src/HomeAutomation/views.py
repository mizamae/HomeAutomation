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
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.http import Http404 
from django.http import HttpResponse
from django.shortcuts import render, render_to_response
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

import utils.BBDD

from .constants import REGISTERS_DB_PATH,GIT_PATH
import DevicesAPP.forms
import DevicesAPP.models
from Events.consumers import PublishEvent
import HomeAutomation.models

#import LocalDevicesAPP.models

logger = logging.getLogger("project")


class Home(generic.TemplateView):
    template_name = "home.html"

class AboutPage(generic.TemplateView):
    template_name = "about.html"

@method_decorator(login_required, name='dispatch')    
class AddDevice(generic.TemplateView):
    template_name = "adddevice.html"
    
    def get_context_data(self, **kwargs):
        context = super(AddDevice, self).get_context_data(**kwargs)
        context['Status'] = 'Init View'
        return context
    
@method_decorator(login_required, name='dispatch')    
class AdvancedDevice(generic.TemplateView):
    template_name = "advanced_device.html"
    def get(self, request):
        from Events.models import EventModel
        EVTs=EventModel.objects.all()
        return render(request, self.template_name,{'events':EVTs})

@login_required
def ShowDeviceList(request):
    '''OK BRANCH'''
    # DVs=RemoteDevicesAPP.models.Devices.objects.all()
    # numrows=len(DVs)
    # return render(request, 'showdevices.html',{'numrows':numrows,'deviceList':DVs})
    DVs=DevicesAPP.models.Devices.objects.all()
    
    remote_DVs=DVs.filter(Type__Connection='REMOTE')
    numrows_remote=len(remote_DVs)
    
    local_DVs=DVs.filter(Type__Connection='LOCAL')
    numrows_local=len(local_DVs)
    
    memory_DVs=DVs.filter(Type__Connection='MEMORY')
    numrows_memory=len(memory_DVs)
    
    return render(request, 'showdevices.html',{'numrows_remote':numrows_remote,'RemotedeviceList':remote_DVs,
                                               'numrows_local':numrows_local,'LocaldeviceList':local_DVs,
                                               'numrows_memory':numrows_memory,'MemorydeviceList':memory_DVs,})


@user_passes_test(lambda u: u.is_superuser)
def settimezone(request):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return HttpResponseRedirect(reverse('advancedDevice'))
    else:
        return render(request, 'timezones.html', {'timezones': pytz.common_timezones})

@user_passes_test(lambda u: u.has_perm('HomeAutomation.view_schedules'))
def viewSchedules(request):
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('home'))
    else:
        SCHDs=HomeAutomation.models.MainDeviceVarWeeklyScheduleModel.objects.all().order_by('-Active')
        VARs=[]
        for SCHD in SCHDs:
            if not SCHD.Var in VARs:
                VARs.append(SCHD.Var)
        now=datetime.datetime.now()
        return render(request,'schedulesList.html',
                          {'DJNGO_HOUR':now.hour,'VARs':VARs,'SCHDs':SCHDs})   

@user_passes_test(lambda u: u.has_perm('HomeAutomation.activate_schedule'))
def activateSchedule(request,pk):
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('home'))
    else:
        SCHD=HomeAutomation.models.MainDeviceVarWeeklyScheduleModel.objects.get(pk=pk)
        SCHD.set_Active(value=True)
        return HttpResponseRedirect(reverse('viewSchedules'))

@user_passes_test(lambda u: u.has_perm('HomeAutomation.edit_schedule'))
def modifySchedule(request,pk,value,sense):
    import decimal
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('home'))
    else:
        SCHD=HomeAutomation.models.MainDeviceVarWeeklyScheduleModel.objects.get(pk=pk)
        SCHD.modify_schedule(value=value,sense=sense)
        return HttpResponseRedirect(reverse('viewSchedules'))

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
@user_passes_test(lambda u: u.has_perm('Devices.add_device'))
def DeleteDevice(request,devicename):

    if devicename!='':   
        try:
            DV=DevicesAPP.models.Devices.objects.get(DeviceName=devicename)
            DV.delete()
        except:
            logger.info('Error!! The device with name ' + devicename + ' does not exist in the database')                 
    return HttpResponseRedirect(reverse('devlist'))




@login_required
@user_passes_test(lambda u: u.has_perm('Devices.add_device'))
def adminSetCustomLabels(request,devicePK):
    if request.method == 'POST':
        DeviceName=request.POST['DeviceName']
        DV=DevicesAPP.models.Devices.objects.get(pk=devicePK)

        #datagrams=DevicesAPP.models.getDatagramStructure(devicetype=device.Type.pk)
        DGs=DevicesAPP.models.DatagramModel.objects.filter(DeviceType=DV.Type)
        
        form = DevicesAPP.forms.DatagramCustomLabelsForm(request.POST,DV=DV,DGs=DGs)
        if form.is_valid():
            DeviceName=form.cleaned_data['DeviceName']
            CustomLabels=form.get_variablesLabels()
            DV.CustomLabels=json.dumps(CustomLabels)
            DV.save()
            DV.updateAutomationVars()
            state='FinishedOK'
        return render(request, 'admin/customLabels.html',{'Status':state,'DeviceName':DV.DeviceName.upper(),'Form': form})
    else:
        DV=DevicesAPP.models.Devices.objects.get(pk=devicePK)
            
        DGs=DevicesAPP.models.DatagramModel.objects.filter(DeviceType=DV.Type)
        form=DevicesAPP.forms.DatagramCustomLabelsForm(None,DV=DV,DGs=DGs)
        state='RegisteredOK'
        return render(request, 'admin/customLabels.html',{'Status':state,'DeviceName':DV.Name.upper(),'Form': form})
            
@login_required
@user_passes_test(lambda u: u.has_perm('Devices.view_report'))
def viewReports(request,pk=None):
    if pk==None:
        ReportItems=DevicesAPP.models.ReportItems.objects.all()
        RPs=DevicesAPP.models.ReportModel.objects.all()
        elements=[]
        reportTitles=[]
        for RP in RPs:
            reportTitles.append(RP.ReportTitle)
        return render(request, 'reportItemsList.html',{'reportTitles':reportTitles,'items':ReportItems})
    else:
        #from HomeAutomation.tasks import checkReportAvailability            
        #checkReportAvailability()        
        ReportItem=DevicesAPP.models.ReportItems.objects.get(pk=pk)
        data=json.dumps(ReportItem.Report.getReportData(toDate=ReportItem.toDate)[0])
        return render(request, 'reportTemplate.html',{'reportTitle':ReportItem.Report.ReportTitle,
                                                            'fromDate':ReportItem.fromDate,
                                                            'toDate':ReportItem.toDate,
                                                            'reportData':data})
    return Http404

@login_required
@user_passes_test(lambda u: u.has_perm('Devices.view_report'))
def previewReport(request,title):
    Report=DevicesAPP.models.ReportModel.objects.get(ReportTitle=title)
    ReportData,fromDate,toDate=Report.getReportData()
    return render(request, 'reportTemplate.html',{'reportTitle':Report.ReportTitle,
                                                        'fromDate':fromDate,
                                                        'toDate':toDate,
                                                        'reportData':json.dumps(ReportData)})
                                                        
@login_required
@user_passes_test(lambda u: u.has_perm('Devices.add_report'))
def deleteReport(request,pk):
    if pk!=None:
        ReportItem=DevicesAPP.models.ReportItems.objects.get(pk=pk)
        ReportItem.delete()
    return HttpResponseRedirect(reverse('viewReports'))
    

        
@login_required
@user_passes_test(lambda u: u.has_perm('Devices.add_report'))

@login_required    
def device_report(request):
     
    if request.method == 'POST': # the form has been submited
        form = DevicesAPP.forms.DeviceGraphs(request.POST)
        
        #logger.debug(str(request.POST))
        if form.is_valid():
            devicename=form.cleaned_data['DeviceName']
            fromDate=form.cleaned_data['fromDate']
            toDate=form.cleaned_data['toDate']
            
            form_clean = DevicesAPP.forms.DeviceGraphs({'DeviceName':form['DeviceName'].value(),'fromDate':fromDate,'toDate':toDate})
            
            fromDate=fromDate-fromDate.utcoffset() 
            toDate=toDate-toDate.utcoffset()                 

            try:
                DV=DevicesAPP.models.Devices.objects.get(DeviceName=devicename)
            except DevicesAPP.models.Devices.DoesNotExist: 
                DV='MainUnit'
            
            charts=[]
            if DV!='MainUnit':  # a device is selected
                #logger.info('The device is a '+str(DV.Type))
                #sampletime=DV.Sampletime
                DGs=DevicesAPP.models.DatagramModel.objects.filter(DeviceType=DV.Type)
                
                if len(DGs)>0:
                    i=0
                    for DG in DGs:
                        datagram_info=DG.getStructure()
                        sampletime=datagram_info['sample']*DV.Sampletime
                        Labeliterable=[]
                        if DV.CustomLabels!='':
                            CustomLabels=json.loads(DV.CustomLabels)
                            labels=CustomLabels[DG.Identifier]
                            for name in datagram_info['names']:
                                Labeliterable.append(labels[name])
                        else:
                            for name in datagram_info['names']:
                                IT=DevicesAPP.models.DatagramItemModel.objects.get(pk=int(name.split('_')[0]))
                                Labeliterable.append(IT.getHumanName())
                    
                        table=str(DV.pk)+'_'+str(datagram_info['pk'])
                        names=datagram_info['names'][:]
                        names.insert(0,'timestamp')
                        types=datagram_info['types']
                        types.insert(0,'datetime')
                        labels=Labeliterable
                        labels.insert(0,'timestamp')
                        plottypes=datagram_info['plottypes']
                        plottypes.insert(0,'timestamp')
                        
                        chart=generateChart(table=table,fromDate=fromDate,toDate=toDate,names=names,types=types,
                                            labels=labels,plottypes=plottypes,sampletime=sampletime)
                         
                        #logger.debug(json.dumps(chart))    
                         
                        charts.append(chart)                                           
            else:
                #logger.info('The device is the Main Unit')
                IOs=Master_GPIOs.models.IOmodel.objects.all()
                MainVars=HomeAutomation.models.MainDeviceVarModel.objects.all()
                if len(IOs)>0:
                    for table in ('inputs','outputs'):
                        if table=='inputs':
                            direction='IN'
                        else:
                            direction='OUT'
                        names=[]
                        types=[]
                        labels=[]
                        plottypes=[]
                        for IO in IOs:
                            if IO.direction==direction:
                                names.append(str(IO.pin))
                                types.append('digital')
                                labels.append(IO.label)
                                plottypes.append('line')
                        
                        names.insert(0,'timestamp')
                        types.insert(0,'datetime')
                        labels.insert(0,'timestamp')
                        plottypes.insert(0,'timestamp')
                        
                        chart=generateChart(table=table,fromDate=fromDate,toDate=toDate,names=names,types=types,
                                            labels=labels,plottypes=plottypes,sampletime=0)
                         
                        #logger.debug(json.dumps(chart))    
                        charts.append(chart)
                if len(MainVars)>0:
                    table='MainVariables'
                    names=[]
                    types=[]
                    labels=[]
                    plottypes=[]
                    for Var in MainVars:
                        names.append(Var.pk)
                        types.append('analog')
                        labels.append(Var.Label)
                        plottypes.append(Var.PlotType)
                    
                    names.insert(0,'timestamp')
                    types.insert(0,'datetime')
                    labels.insert(0,'timestamp')
                    plottypes.insert(0,'timestamp')
                    
                    chart=generateChart(table=table,fromDate=fromDate,toDate=toDate,names=names,types=types,
                                        labels=labels,plottypes=plottypes,sampletime=0)
                     
                    #logger.debug(json.dumps(chart))    
                     
                    charts.append(chart) 
            return render(request, 'DeviceGraph.html', {'devicename':devicename.replace('_',' '),'chart': json.dumps(charts),'Form':form_clean})
        else:
            return render(request, 'DeviceGraph.html',{'Form': form})
    else:
        form=DevicesAPP.forms.DeviceGraphs()
        return render(request, 'DeviceGraph.html',{'Form': form})

def generateChart(table,fromDate,toDate,names,types,labels,plottypes,sampletime):
    applicationDBs=DevicesAPP.BBDD.DIY4dot0_Databases(registerDBPath=REGISTERS_DB_PATH) 
    
    chart={}
    chart['title']=table
    chart['cols']=[]
    i=0
    tempname=[]
    vars=''
    for name,type,label,plottype in zip(names,types,labels,plottypes):
        #logger.info(str(name))
        vars+='"'+str(name)+'"'+','
        if type=='analog':
            tempname.append({'label':label,'type':type,'plottype':plottype})
        elif type=='digital':
            labels=label.split('$')
            tempname.append({'label':labels,'type':type,'plottype':plottype})
        else:
            tempname.append({'label':label,'type':type,'plottype':plottype})
        
    vars=vars[:-1]
    chart['cols'].append(tempname)    
    
    limit=10000
    sql='SELECT '+vars+' FROM "'+ table +'" WHERE timestamp BETWEEN "' + str(fromDate).split('+')[0]+'" AND "'+str(toDate).split('+')[0] + '" ORDER BY timestamp ASC LIMIT ' + str(limit)
    #logger.info('SQL:' + sql)
    
    # data_rows=applicationDBs.registersDB.retrieve_from_table(sql=sql,single=False,values=(None,))
    df=pd.read_sql_query(sql=sql,con=applicationDBs.registersDB.conn,index_col='timestamp')
    
    if not df.empty:
        
        # TO FORCE THAT THE INITIAL ROW CONTAINS THE INITIAL DATE
        addedtime=pd.to_datetime(arg=df.index.values[0])-fromDate.replace(tzinfo=None)
        if addedtime>datetime.timedelta(minutes=1):
            ts = pd.to_datetime(fromDate.replace(tzinfo=None))
            new_row = pd.DataFrame([df.iloc[0].values], columns = df.columns, index=[ts])
            df=pd.concat([pd.DataFrame(new_row),df], ignore_index=False)
            
        # TO FORCE THAT THE LAST ROW CONTAINS THE END DATE
        addedtime=toDate.replace(tzinfo=None)-pd.to_datetime(arg=df.index.values[-1])
        if addedtime>datetime.timedelta(minutes=1):
            ts = pd.to_datetime(toDate.replace(tzinfo=None))
            new_row = pd.DataFrame([df.iloc[-1].values], columns = df.columns, index=[ts])
            df=pd.concat([df,pd.DataFrame(new_row)], ignore_index=False)
        
        # RESAMPLING DATA TO 1 MINUTE RESOLUTION AND INTERPOLATING VALUES
        df_res=df.resample('1T').mean()
        df_int=df_res.interpolate(method='zero')
    else:
        sql='SELECT '+vars+' FROM "'+ table +'" ORDER BY timestamp DESC LIMIT 1'
        df=pd.read_sql_query(sql=sql,con=applicationDBs.registersDB.conn,index_col='timestamp')
        if not df.empty:
            values=np.concatenate([df.values,df.values])
        # TO FORCE THAT THE INITIAL ROW CONTAINS THE INITIAL DATE
        ts_ini = pd.to_datetime(fromDate.replace(tzinfo=None))
        ts_end = pd.to_datetime(toDate.replace(tzinfo=None))
        df = pd.DataFrame(data=values,index=[ts_ini,ts_end],columns=df.columns)
        df_int=df
            
    tempStats={'number':5,'num_rows':df.count(numeric_only=True).tolist(),'mean':[],'max':df.max(numeric_only=True).tolist(),'min':df.min(numeric_only=True).tolist(),'on_time':[],'off_time':[]}
    
    for name,type in zip(names,types):
        if type=='digital':
            def dec2bin(x):
                data=[]
                for i in range(0,8):
                    try:
                        x=int(x)
                        data.append(1 if (x & (1<<int(i)))>0 else 0)
                    except:
                        data.append(None)
                return data
                    
            try:
                df[name]=df[name].apply(func=dec2bin)
                from HomeAutomation.models import AdditionalCalculationsModel
                kk=pd.DataFrame(df[name])
                CALC=AdditionalCalculationsModel(df=kk,key=name)
                tempStats['on_time'].append(CALC.duty(level=True,absoluteValue=True))
                tempStats['off_time'].append(CALC.duty(level=False,absoluteValue=True))
            except KeyError:
                tempStats['on_time'].append(None)
                tempStats['off_time'].append(None)
            

            tempStats['mean'].append(None)
        elif type=='analog':
            try:
                # AN ERROR CAN OCCUR IF THE VARIABLE HAS NO VALUE ALONG THE TIMESPAN
                tempStats['mean'].append(df_int[str(name)].mean())
            except KeyError:
                tempStats['mean'].append(None)
            tempStats['on_time'].append(None)
            tempStats['off_time'].append(None)
    
    tempX2 = [x / 1000000 for x in df.index.values.tolist()]
    # TRANSFORMING THE NANs TO NONEs TO AVOID JSON ENCODING ISSUES
    tempData=df.where(pd.notnull(df), None).values.tolist()
    
    for row,timestamp in zip(tempData,tempX2):
        row.insert(0,timestamp)   
         
    chart['rows']=tempData
    chart['statistics']=tempStats
    #print (str(chart))
    return chart
    
@login_required
@user_passes_test(lambda u: u.has_perm('Devices.view_plots'))
def AdvancedDevicepage(request,pk):
    import json
    DV=DevicesAPP.models.Devices.objects.get(pk=pk)
    LatestData=DV.getLatestData()
    return render(request, DV.Type.Code+'.html',
        {'Device':DV,'Latest':LatestData})

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
