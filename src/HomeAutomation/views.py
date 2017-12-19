# coding: utf-8
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from django.utils import timezone
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

import Devices.BBDD
import Devices.GlobalVars
#import RemoteDevices.HTTP_client
import Devices.HTTP_client
import Devices.Reports
import Devices.Requests
import Devices.XML_parser
import Devices.forms
import Devices.models
import Master_GPIOs.models
from Events.consumers import PublishEvent
import HomeAutomation.models

#import LocalDevices.models

import xml.etree.ElementTree as ET

logger = logging.getLogger("project")


class HomePage(generic.TemplateView):
    template_name = "home.html"
            
class HomePageDevice(generic.TemplateView):
    template_name = "home_device.html"

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
    # DVs=RemoteDevices.models.DeviceModel.objects.all()
    # numrows=len(DVs)
    # return render(request, 'showdevices.html',{'numrows':numrows,'deviceList':DVs})
    DVs=Devices.models.DeviceModel.objects.all()
    
    remote_DVs=DVs.filter(Type__Connection='REMOTE')
    numrows_remote=len(remote_DVs)
    
    local_DVs=DVs.filter(Type__Connection='LOCAL')
    numrows_local=len(local_DVs)
    
    memory_DVs=DVs.filter(Type__Connection='MEMORY')
    numrows_memory=len(memory_DVs)
    
    return render(request, 'showdevices.html',{'numrows_remote':numrows_remote,'RemotedeviceList':remote_DVs,
                                               'numrows_local':numrows_local,'LocaldeviceList':local_DVs,
                                               'numrows_memory':numrows_memory,'MemorydeviceList':memory_DVs,})

@user_passes_test(lambda u: u.has_perm('HomeAutomation.change_state'))
def ToggleDevice(request,devicename):
    Devices.Requests.toggle_requests(DeviceName=devicename)
    return HttpResponseRedirect(reverse('devlist'))

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
        SCHD.Active=True
        SCHD.save()
        return HttpResponseRedirect(reverse('viewSchedules'))

@user_passes_test(lambda u: u.has_perm('HomeAutomation.edit_schedule'))
def modifySchedule(request,pk,value,sense):
    import decimal
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('home'))
    else:
        SCHD=HomeAutomation.models.MainDeviceVarWeeklyScheduleModel.objects.get(pk=pk)
        if value=='LValue':
            if sense=='-':
                SCHD.LValue-=decimal.Decimal.from_float(0.5)
            else:
                SCHD.LValue+=decimal.Decimal.from_float(0.5)
            SCHD.save()
        elif value=='HValue':
            if sense=='-':
                SCHD.HValue-=decimal.Decimal.from_float(0.5)
            else:
                SCHD.HValue+=decimal.Decimal.from_float(0.5)
            SCHD.save()
        elif value=='REFValue':
            if SCHD.Var.Value==SCHD.HValue:
                newValue=SCHD.LValue
            else:
                newValue=SCHD.HValue
            SCHD.Var.update_value(newValue=newValue,writeDB=True)
            
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
            DV=Devices.models.DeviceModel.objects.get(DeviceName=devicename)
            DV.delete()
        except:
            logger.info('Error!! The device with name ' + devicename + ' does not exist in the database')                 
    return HttpResponseRedirect(reverse('devlist'))

@login_required
@user_passes_test(lambda u: u.has_perm('Devices.add_device'))
def ConfDevice(request,code):
    '''OK BRANCH'''
    state=''
    if request.method == 'POST': # the form has been submited
        if 'DeviceCode' in request.POST: # the device form has been submitted
            form = Devices.forms.DeviceForm(request.POST)
            code=str(form['DeviceCode'].value())
            name=form['DeviceName'].value()
            logger.info('Trying to register the device with code ' + code + ' with the new name ' + name)  
            # Check if the form is valid:
            if form.is_valid():
                logger.info('Form submitted is valid')  
                code=form.cleaned_data['DeviceCode']
                name=form.cleaned_data['DeviceName']
                IP=form.cleaned_data['DeviceIP']
                DeviceType =form.cleaned_data['Type']  
                Sampletime =form.cleaned_data['Sampletime']  
                DeviceState=form.cleaned_data['DeviceState']
                logger.warning('Found a device type '+str(DeviceType))
                code=int(code)
                DV=Devices.models.DeviceModel(DeviceName=name,DeviceCode=code,DeviceIP=IP,Type=DeviceType,
                                                                 DeviceState=DeviceState,Sampletime=Sampletime)
                DV.save(update_fields=[])
                state='RegisteredOK'
            
                DGs=Devices.models.DatagramModel.objects.filter(DeviceType=DV.Type)
                form=Devices.forms.DatagramCustomLabelsForm(None,DV=DV,DGs=DGs)
    
                return render(request,'reqconfdevice.html',
                          {'Status':state,'DeviceName':name.upper(),'Form': form})                
            else:
                logger.warning('Error!!: Form submitted is NOT valid')  
                logger.warning('Error!!: ' + str(form.errors))  
                state='FieldNoOK'
            return render(request,'reqconfdevice.html',
                          {'Status':state,'Form': form})
        else: # the datagram custom labels form has been submitted
            DeviceName=request.POST['DeviceName']
            DV=Devices.models.DeviceModel.objects.get(DeviceName=DeviceName)
            DGs=Devices.models.DatagramModel.objects.filter(DeviceType=DV.Type)
            form=Devices.forms.DatagramCustomLabelsForm(request.POST,DV=DV,DGs=DGs)
            if form.is_valid():
                DeviceName=form.cleaned_data['DeviceName']
                CustomLabels=form.get_variablesLabels()
                DV.CustomLabels=json.dumps(CustomLabels)
                DV.save(update_fields=[])
                DV.updateAutomationVars()
                #print('OK!!!')
                state='FinishedOK'
            return render(request,'reqconfdevice.html',
                          {'Status':state,'Form': form})
    else:   # the page is first loaded
        try :
            code=int(code)
        except ValueError:
            form=Devices.forms.DeviceForm(initial={'DeviceName':'','DeviceCode':'','DeviceIP':''})
            state='URLNoOK'
            return render(request, 'reqconfdevice.html',{'Status':state,'Form': form})
           
        server='http://10.10.10.'+str(code)
        #server='http://127.0.0.1'
        HTTPrequest=Devices.HTTP_client.HTTP_requests(server=server)  
        (status,root)=HTTPrequest.request_confXML(xmlfile=Devices.GlobalVars.DEVICES_CONFIG_FILE)
        xmlparser=Devices.XML_parser.XMLParser(xmlroot=root)
        
        if status==200:
            (DEVICE_TYPE,DEVICE_CODE,DEVICE_IP) =xmlparser.parseDeviceConfFile()
            try:
                Type=Devices.models.DeviceTypeModel.objects.get(Code=DEVICE_TYPE)
            except Devices.models.DeviceTypeModel.DoesNotExist: 
                Type=None
                
            lastRow=Devices.models.DeviceModel.objects.all().count()                     
            DeviceName='Device'+str(lastRow+1)
            DeviceType=DEVICE_TYPE
            DEVICE_CODE=lastRow+1+Devices.GlobalVars.IP_OFFSET
            DeviceIP='10.10.10.'+str(DEVICE_CODE)
            payload={'DEVC':str(DEVICE_CODE)}
            (status,r)=HTTPrequest.request_orders(order='SetConf.htm',payload=payload)
            if status==200:
                logger.info('Device code assigned OK to ' +str(DEVICE_CODE)+'. Devicename missing')                      
                form=Devices.forms.DeviceForm(initial={'DeviceName':DeviceName,'Type':Type,'DeviceCode':DEVICE_CODE,'DeviceIP':DeviceIP})
                state='ConfigOK'
            else:
                logger.warning('Device responded to the request of SetConf with HTTP code '+ str(status)) 
                DEVICE_CODE=0
                DeviceIP='10.10.10.0'
                form=Devices.forms.DeviceForm(initial={'DeviceName':DeviceName,'Type':Type,'DeviceCode':DEVICE_CODE,'DeviceIP':DeviceIP})
                state='ConfigNoOK'
                return render(request,'adddevice.html',{'Status':state})
            return render(request, 'reqconfdevice.html',{'Status':state,'Form': form})
    
        else:
            logger.warning('Device responded to the request of Conf with HTTP code '+ str(status)) 
            form=Devices.forms.DeviceForm(initial={'DeviceName':'','DeviceCode':'','DeviceIP':''})
            state='NoDevice'
        return render(request, 'reqconfdevice.html',{'Status':state,'Form': form})   
           
    return render(request, 'reqconfdevice.html',{'Status':state,'Form': form})  

@login_required
@user_passes_test(lambda u: u.has_perm('Devices.add_device'))
def adminSetCustomLabels(request,devicePK):
    if request.method == 'POST':
        DeviceName=request.POST['DeviceName']
        DV=Devices.models.DeviceModel.objects.get(pk=devicePK)

        #datagrams=Devices.models.getDatagramStructure(devicetype=device.Type.pk)
        DGs=Devices.models.DatagramModel.objects.filter(DeviceType=DV.Type)
        
        form = Devices.forms.DatagramCustomLabelsForm(request.POST,DV=DV,DGs=DGs)
        if form.is_valid():
            DeviceName=form.cleaned_data['DeviceName']
            CustomLabels=form.get_variablesLabels()
            DV.CustomLabels=json.dumps(CustomLabels)
            DV.save(update_fields=[])
            DV.updateAutomationVars()
            state='FinishedOK'
        return render(request, 'admin/customLabels.html',{'Status':state,'DeviceName':DV.DeviceName.upper(),'Form': form})
    else:
        DV=Devices.models.DeviceModel.objects.get(pk=devicePK)
            
        DGs=Devices.models.DatagramModel.objects.filter(DeviceType=DV.Type)
        form=Devices.forms.DatagramCustomLabelsForm(None,DV=DV,DGs=DGs)
        state='RegisteredOK'
        return render(request, 'admin/customLabels.html',{'Status':state,'DeviceName':DV.DeviceName.upper(),'Form': form})
            
@login_required
@user_passes_test(lambda u: u.has_perm('Devices.view_report'))
def viewReports(request,pk=None):
    if pk==None:
        ReportItems=Devices.models.ReportItems.objects.all()
        RPs=Devices.models.ReportModel.objects.all()
        elements=[]
        reportTitles=[]
        for RP in RPs:
            reportTitles.append(RP.ReportTitle)
            #logger.info('Report: ' + Item.Report.ReportTitle)
        # for Item in ReportItems:
            # elements.append(Item)
        #logger.info('Found : ' + str(elements))
        return render(request, 'reportItemsList.html',{'reportTitles':reportTitles,'items':ReportItems})
    else:
        #from HomeAutomation.tasks import checkCustomCalculations            
        #checkCustomCalculations()        
        ReportItem=Devices.models.ReportItems.objects.get(pk=pk)
        return render(request, 'reportTemplate.html',{'reportTitle':ReportItem.Report.ReportTitle,
                                                            'fromDate':ReportItem.fromDate,
                                                            'toDate':ReportItem.toDate,
                                                            'reportData':ReportItem.data})
    return Http404

@login_required
@user_passes_test(lambda u: u.has_perm('Devices.view_report'))
def previewReport(request,title):
    Report=Devices.models.ReportModel.objects.get(ReportTitle=title)
    ReportData,fromDate,toDate=Report.getReport()
    ReportItem=Devices.models.ReportItems(Report=Report,fromDate=fromDate,toDate=toDate,data=json.dumps(ReportData))
    return render(request, 'reportTemplate.html',{'reportTitle':ReportItem.Report.ReportTitle,
                                                        'fromDate':ReportItem.fromDate,
                                                        'toDate':ReportItem.toDate,
                                                        'reportData':ReportItem.data})
                                                        
@login_required
@user_passes_test(lambda u: u.has_perm('Devices.add_report'))
def deleteReport(request,pk):
    if pk!=None:
        ReportItem=Devices.models.ReportItems.objects.get(pk=pk)
        ReportItem.delete()
    return HttpResponseRedirect(reverse('viewReports'))
    
@login_required
@user_passes_test(lambda u: u.has_perm('Devices.add_device'))
def ajax_get_data_for_devicetype(request,devicetypePK):
    if request.is_ajax():
        DV=Devices.models.DeviceTypeModel.objects.get(pk=devicetypePK)
        info={'Connection':DV.Connection}
        return HttpResponse(json.dumps(info))
    else:
        return HttpResponse(json.dumps([]))

@login_required
@user_passes_test(lambda u: u.has_perm('HomeAutomation.add_automationrule'))
def ajax_get_orders_for_device(request,devicePK):
    if request.is_ajax():
        DV=RemoteDevices.models.DeviceModel.objects.get(pk=devicePK)
        orders=Devices.models.CommandModel.objects.filter(DeviceType=DV.Type)
        info=[]
        if len(orders)>0:
            for order in orders:
                info.append({'Identifier':order.Identifier,'HumanTag':order.HumanTag})
                
        return HttpResponse(json.dumps(info))
    else:
        return HttpResponse(json.dumps([]))
        
@login_required
@user_passes_test(lambda u: u.has_perm('Devices.add_report'))
def reportbuilder(request,number=0):
    
    applicationDBs=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                      configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH) 
    form_data={'ReportTitle':'','Periodicity':2,'DataAggregation':0}
    form=Devices.forms.ReportForm(form_data)  
    if request.method == 'POST':
        json_data=request.body.decode('utf-8')
        #logger.info('Received the post! - '+ json_data)
        data = json.loads(json_data)
        #logger.info('JSON loaded OK')
        ReportTitle=str(data[0]['report_title'])
        Periodicity=data[0]['Periodicity']
        DataAggregation=data[0]['DataAggregation']
        ReportContentJSON=json_data
        #logger.debug('Report content: ' + ReportContentJSON)             
        form_data={'ReportTitle':ReportTitle,'Periodicity':Periodicity,'DataAggregation':DataAggregation,'ReportContentJSON':ReportContentJSON}
        form=Devices.forms.ReportForm(form_data)
        #logger.info('Trying to create a report with the title ' + ReportTitle) 
        if form.is_valid(): 
            #logger.info('Form is valid!')
            REP=Devices.models.ReportModel.objects.create_Report(ReportTitle=ReportTitle,Periodicity=Periodicity,DataAggregation=DataAggregation,ReportContentJSON=ReportContentJSON)
            
            #applicationDBs.devicesDB.insert_row(SQL_statement=applicationDBs.devicesDB.SQLinsertReport_statement,row_values=(ReportTitle,ReportCode,ReportContentJSON))
            return HttpResponse(json.dumps({'Confirmation': 'OK'})) 
        else:
            logger.error('Form error ' + str(form.errors))
            return HttpResponse(json.dumps({'Error': form.errors})) 
    else:
        info=Devices.models.getAllVariables()
        #logger.debug(info)       
        return render(request, 'reportconfigurator.html', {'Form':form,'data': json.dumps(info)})    
    
    return render(request, 'reportconfigurator.html', {'Form':form,'data': json.dumps({'Error':'Database is not reachable'})})    

@login_required    
def device_report(request):
     
    if request.method == 'POST': # the form has been submited
        form = Devices.forms.DeviceGraphs(request.POST)
        
        #logger.debug(str(request.POST))
        if form.is_valid():
            devicename=form.cleaned_data['DeviceName']
            fromDate=form.cleaned_data['fromDate']
            toDate=form.cleaned_data['toDate']
            
            form_clean = Devices.forms.DeviceGraphs({'DeviceName':form['DeviceName'].value(),'fromDate':fromDate,'toDate':toDate})
            
            fromDate=fromDate-fromDate.utcoffset() 
            toDate=toDate-toDate.utcoffset()                 

            try:
                DV=Devices.models.DeviceModel.objects.get(DeviceName=devicename)
            except Devices.models.DeviceModel.DoesNotExist: 
                DV='MainUnit'
            
            charts=[]
            if DV!='MainUnit':  # a device is selected
                #logger.info('The device is a '+str(DV.Type))
                #sampletime=DV.Sampletime
                DGs=Devices.models.DatagramModel.objects.filter(DeviceType=DV.Type)
                
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
                                IT=Devices.models.DatagramItemModel.objects.get(pk=int(name.split('_')[0]))
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
        form=Devices.forms.DeviceGraphs()
        return render(request, 'DeviceGraph.html',{'Form': form})

def generateChart(table,fromDate,toDate,names,types,labels,plottypes,sampletime):
    applicationDBs=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                      configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH) 
    
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
    
    data_rows=applicationDBs.registersDB.retrieve_from_table(sql=sql,single=False,values=(None,))
    
    tempData=[]
    tempStats={'number':5,'num_rows':[],'mean':[],'max':[],'min':[],'on_time':[],'off_time':[]}
    isFirstRow=True
    
    local_tz=get_localzone()
    
    if data_rows==[] or data_rows==None: # this may happen in asynchronous datagrams
        # get the last row from the DB
        temp=[]
        sql='SELECT '+vars+' FROM "'+ table +'" ORDER BY timestamp DESC LIMIT 1'
        row=applicationDBs.registersDB.retrieve_from_table(sql=sql,single=True,values=(None,))
        if row != None:
            
            for k,col in enumerate(row):
                if types[k]=='analog':
                    temp.append(col)
                elif types[k]=='digital':
                    data=[]
                    for i in range(0,8):
                        if col!=None:
                            data.append(1 if (col & (1<<int(i)))>0 else 0)
                        else:
                            data.append(None)
                    temp.append(data)
                else:   # for the datetime
                    temp.append(col)
        else:
            temp.append(fromDate)
            for k,var in enumerate(vars.split(',')):
                if types[k]=='analog':
                    temp.append(None)
                elif types[k]=='digital':
                    data=[]
                    for i in range(0,8):
                            data.append(None)
                    temp.append(data)
        now = timezone.now()
        localdate = fromDate
        localdate=localdate+localdate.utcoffset() 
        fecha={'v':'Date('+str(localdate.year)+','+str(localdate.month-Devices.GlobalVars.daysmonths_offset)+','+str(localdate.day)+','+str(localdate.hour)+','+str(localdate.minute)+','+str(1)+')'}
        del temp[0] #removes the column with the original datetimes
        temp.insert(0, fecha)
        tempData.append(temp)
        # extrapolate the last row from the DB
        temp=[]
        if row != None:
            for k,col in enumerate(row):
                if types[k]=='analog':
                    temp.append(col)
                elif types[k]=='digital':
                    data=[]
                    for i in range(0,8):
                        if col!=None:
                            data.append(1 if (col & (1<<int(i)))>0 else 0)
                        else:
                            data.append(None)
                    temp.append(data)
                else:   # for the datetime
                    temp.append(col)
        else:
            temp.append(toDate)
            for k,var in enumerate(vars.split(',')):
                if types[k]=='analog':
                    temp.append(None)
                elif types[k]=='digital':
                    data=[]
                    for i in range(0,8):
                            data.append(None)
                    temp.append(data)
                
        fecha={'v':'Date('+str(toDate.year)+','+str(toDate.month-Devices.GlobalVars.daysmonths_offset)+','+str(toDate.day)+','+str(toDate.hour)+','+str(toDate.minute)+','+str(toDate.second)+')'}
        del temp[0] #removes the column with the original datetimes
        temp.insert(0, fecha)
        tempData.append(temp)           
    else:
        if sampletime==0:
            row_ini=list(data_rows[0])
            row_ini[0]=fromDate.replace(tzinfo=None)
            data_rows.insert(0,tuple(row_ini)) # introduces in the first position a row dated in fromDate with the values of the first real register
            row_ini=data_rows[1]
            row_ini=list(data_rows[len(data_rows)-1])
            row_ini[0]=toDate.replace(tzinfo=None)
            data_rows.append(tuple(row_ini)) # introduces in the last position a row dated in toDate with the values of the last real register
                 
        for row in data_rows:
            temp=[]
            localdate = local_tz.localize(row[0])
            localdate=localdate+localdate.utcoffset() 
            fecha={'v':'Date('+str(localdate.year)+','+str(localdate.month-Devices.GlobalVars.daysmonths_offset)+','+str(localdate.day)+','+str(localdate.hour)+','+str(localdate.minute)+','+str(localdate.second)+')'}
            #logger.info(str(fecha))      
            if isFirstRow==False:
                sampletime=row[0]-prevRow[0]
#             if row[-1]!=None:
#                 tempStats['num_rows']+=1
            k=0
            for col in row:
                if col=='':
                    col=None
                if types[k]=='analog':
                    temp.append(col)
                elif types[k]=='digital':
                    data=[]
                    for i in range(0,8):
                        if col!=None:
                            data.append(1 if (col & (1<<int(i)))>0 else 0)
                        else:
                            data.append(None)
                    temp.append(data)
                else:   # for the datetime
                    temp.append(col)
                if col!=None:
                    if k>=1: # to avoid including the timestamp in the statistics
                        if isFirstRow:
                            if types[k]=='analog':
                                tempStats['mean'].append(col)
                                tempStats['max'].append(col)
                                tempStats['min'].append(col)
                                tempStats['num_rows'].append(0)
                                tempStats['on_time'].append(0)
                                tempStats['off_time'].append(0)
                            else:
                                vectON=[]
                                vectOFF=[]
                                for i in range(0,8):
                                    data= 1 if (col & (1<<int(i)))>0 else 0
                                    vectON.append(data*sampletime)
                                    vectOFF.append((not data)*sampletime)
                                tempStats['mean'].append(0)
                                tempStats['max'].append(-10000000)
                                tempStats['min'].append(10000000)
                                tempStats['num_rows'].append(0)
                                tempStats['on_time'].append(vectON)
                                tempStats['off_time'].append(vectOFF)
                        else:
                            #tempStats['mean'][k-1]=(tempStats['mean'][k-1]*(tempStats['number']-1)+col)/tempStats['number'] # moving average
                            try:
                                tempStats['num_rows'][k-1]+=1
                                #logger.debug('COL=' + str(col))
                                if types[k]=='analog':
                                    if tempStats['mean'][k-1]!=None:
                                        tempStats['mean'][k-1]=tempStats['mean'][k-1]+(col-tempStats['mean'][k-1])/tempStats['num_rows'][k-1] # moving average
                                    else:
                                        tempStats['mean'][k-1]=col
                                    if tempStats['max'][k-1]!=None:
                                        if col>tempStats['max'][k-1]:
                                            tempStats['max'][k-1]=col
                                    else:
                                        tempStats['max'][k-1]=col
                                    if tempStats['min'][k-1]!=None:
                                        if col<tempStats['min'][k-1]:
                                            tempStats['min'][k-1]=col
                                    else:
                                        tempStats['min'][k-1]=col
                                elif types[k]=='digital':
                                    for i in range(0,8):
                                        data= 1 if (col & (1<<int(i)))>0 else 0
                                        if tempStats['on_time'][k-1][i]!=None:
                                            tempStats['on_time'][k-1][i]+=data*(sampletime.days*86400+sampletime.seconds)
                                            tempStats['off_time'][k-1][i]+=(not data)*(sampletime.days*86400+sampletime.seconds)
                                        else:
                                            tempStats['on_time'][k-1][i]=data*(sampletime.days*86400+sampletime.seconds)
                                            tempStats['off_time'][k-1][i]=(not data)*(sampletime.days*86400+sampletime.seconds)
                            except IndexError: # this can happen when some variables are added to a datagram and want to show on a same plot the previous and the new datagram (with more variables)
                                if types[k]=='analog':
                                    tempStats['mean'].append(col)
                                    tempStats['max'].append(col)
                                    tempStats['min'].append(col)
                                    tempStats['num_rows'].append(0)
                                    tempStats['on_time'].append(None)
                                    tempStats['off_time'].append(None)
                                else:
                                    tempStats['mean'].append(None)
                                    tempStats['max'].append(None)
                                    tempStats['min'].append(None)
                                    tempStats['num_rows'].append(0)
                                    vectON=[]
                                    vectOFF=[]  
                                    if col!=None:
                                        for i in range(0,8):
                                            data= 1 if (col & (1<<int(i)))>0 else 0
                                            vectON.append(data*(sampletime.days*86400+sampletime.seconds))
                                            vectOFF.append((not data)*(sampletime.days*86400+sampletime.seconds))
                                    else:
                                        for i in range(0,8):
                                            vectON.append(None)
                                            vectOFF.append(None)
                                    tempStats['on_time'].append(vectON)
                                    tempStats['off_time'].append(vectOFF)
                else:
                    if k>=1 and isFirstRow: # to avoid including the timestamp in the statistics
                        if types[k]=='analog':
                            tempStats['mean'].append(None)
                            tempStats['max'].append(None)
                            tempStats['min'].append(None)
                            tempStats['num_rows'].append(0)
                            tempStats['on_time'].append(None)
                            tempStats['off_time'].append(None)
                        else:
                            vectON=[]
                            vectOFF=[]
                            for i in range(0,8):
                                vectON.append(None)
                                vectOFF.append(None)
                            tempStats['mean'].append(None)
                            tempStats['max'].append(None)
                            tempStats['min'].append(None)
                            tempStats['num_rows'].append(0)
                            tempStats['on_time'].append(vectON)
                            tempStats['off_time'].append(vectOFF)
                k+=1
            
            del temp[0] #removes the column with the original datetimes
            temp.insert(0, fecha)
            tempData.append(temp)
            prevRow=row
            isFirstRow=False    
         
    chart['rows']=tempData
    chart['statistics']=tempStats
    #print (str(chart))
    return chart
    
@login_required
@user_passes_test(lambda u: u.has_perm('Devices.view_plots'))
def AdvancedDevicepage(request,pk):
    import json
    DV=Devices.models.DeviceModel.objects.get(pk=pk)
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
                print('Found user : ' + str(usr))
                if usr.profile.tracking:
                    timestamp=timezone.now()
                    applicationDBs=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                      configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH)
                    applicationDBs.insert_track(TimeStamp=timestamp,User=str(usr.email),Latitude=data['lat'],Longitude=data['lon'],Accuracy=data['acc'])
                    usr.profile.Latitude=data['lat']
                    usr.profile.Longitude=data['lon']
                    usr.profile.Accuracy=data['acc']
                    usr.profile.LastUpdated=timestamp
                    usr.profile.save()
                    
        #JSON: {"_type":"location","tid":"MZ","acc":54,"batt":79,"conn":"m","lat":42.8175305,"lon":-1.6015541,"t":"u","tst":1510664016}
        
        # tid: identification of the user
        # acc: Accuracy of the reported location in meters
        # conn: connection type, m for mobile, w for wifi, o for offline
        return HttpResponse(status=204) #The server successfully processed the request and is not returning any content
                
@csrf_exempt
def asynchronous_datagram(request):
    
    if request.method == 'POST':
        #logger.info('Async Request: POST ' + str(request.body))
        applicationDBs=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                      configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH)
        
        xmltext=str(request.body)[1:].replace("'","")
        #logger.info('XmlTEXT ' + xmltext)
#XmlTEXT <X>\n\t<DEV>4</DEV>\t\t<!-- DEVICE CODE-->\n\t<DId>0</DId>\t\t\t\t<!-- DATAGRAM CODE -->\n\t<VAR>0</VAR>\t\t\t\t<!-- STATUS -->\n\t<AV>191,132,122,23</AV>\t\t<!-- T -->\n\t<AV>190,130,122,23</AV>\t\t<!-- RH -->\n</X>
        root = ET.fromstring(xmltext)
        xmlparser=Devices.XML_parser.XMLParser(xmlroot=root)
        (result,datagram)=xmlparser.parseDatagram()
        logger.info('Async Request: Datagram ' + str(datagram))
        if result==0:
            timestamp=timezone.now()  
            deviceCode=datagram[0]
            datagramCode=datagram[1]
            device=Devices.models.DeviceModel.objects.get(DeviceCode=deviceCode)
            datagramModel=Devices.models.DatagramModel.objects.filter(DeviceType=device.Type).filter(Code=int(datagramCode))[0]
            del datagram[0:2]
            if device!=None and datagramModel!=None:
                applicationDBs.insert_device_register(TimeStamp=timestamp, DeviceCode=deviceCode, DeviceName=device.DeviceName, DatagramId=datagramModel.Identifier, 
                                              year=timestamp.year, values=datagram)

        else:
            print('The datagram received was not properly formatted: ' + datagram)
        
    else: #GET
        logger.info('Asynchronous Request with GET format. No longer supported.')

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
    for root, dirs, n in walk(Devices.GlobalVars.GIT_PATH):
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
        PublishEvent(Severity=0,Text=_("%s the latest revision '%s'.") %
              (_("Already at") if not updated else _("Updated to"), revision),Persistent=False)
        
        if updated:
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
