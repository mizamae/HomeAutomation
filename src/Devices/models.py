import os

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

from apscheduler.schedulers.background import BackgroundScheduler
import apscheduler.events as events

from django.dispatch import receiver
from django.db.models.signals import post_save,post_delete,pre_delete
from django.db.models.signals import m2m_changed

from channels.binding.websockets import WebsocketBinding,WebsocketBindingWithMembers 

from Events.consumers import PublishEvent
from Master_GPIOs.models import IOmodel
import HomeAutomation.models
import json
import itertools
import Devices.GlobalVars
import Devices.BBDD

import logging

logger = logging.getLogger("project")
#replace print by logger.info

def path_file_name(instance, filename):
    import os
    filename, file_extension = os.path.splitext(filename)
    return '/'.join(filter(None, (instance.Code, 'thumbnail'+file_extension)))
    
class DeviceTypeModel(models.Model):
    CONNECTION_CHOICES=(
        ('LOCAL','LOCAL'),
        ('REMOTE','REMOTE'),
        ('MEMORY','MEMORY')
    )
    Code = models.CharField(unique=True, max_length=20)
    Description = models.CharField(max_length=100)
    MinSampletime=models.PositiveIntegerField(default=10)
    Connection= models.CharField(choices=CONNECTION_CHOICES, max_length=15)
    Picture = models.ImageField('DeviceType picture',
                                upload_to=path_file_name,
                                null=True,
                                blank=True)
                                
    def __str__(self):
        return self.Code
    
    class Meta:
        verbose_name = _('Device type')
        verbose_name_plural = _('Device types')

@receiver(pre_delete, sender=DeviceTypeModel, dispatch_uid="delete_DeviceTypeModel")
def delete_DeviceTypeModel(sender, instance,**kwargs):
    instance.Picture.delete(False)

def initialize_polling_devices():
    scheduler = BackgroundScheduler()
    url = 'sqlite:///scheduler.sqlite'
    scheduler.add_jobstore('sqlalchemy', url=url)
                    
    def my_listener(event):
        if event.exception:
            try:
                text='The scheduled task '+event.job_id+' reported an error: ' + str(event.traceback) 
                logger.info("APS: " + str(event.traceback))
            except:
                text='Error on scheduler: ' + str(event.exception)
                logger.info("APS: " + str(event.exception))
            PublishEvent(Severity=4,Text=text,Persistent=True)
            #initialize_polling_devices()
        else:
            pass

    scheduler.add_listener(callback=my_listener, mask=events.EVENT_JOB_EXECUTED | events.EVENT_JOB_ERROR)

    try:
        scheduler.start()
    except BaseException as e:
        logger.info('Exception APS: ' + str(e))
    
    DVs=Devices.models.DeviceModel.objects.all()
    if DVs is not None:
        for DV in DVs:
            DV.update_requests(sched=scheduler)
            
def request_callback(DV,DG,jobID,**kwargs): 
    if (DV.Type.Connection=='LOCAL' or DV.Type.Connection=='MEMORY'):
        import Devices.callbacks
        class_=getattr(Devices.callbacks, DV.Type.Code)
        instance=class_(DV)
        status=instance(**kwargs)
    elif DV.Type.Connection=='REMOTE':
        import Devices.HTTP_client
        HTTPrequest=Devices.HTTP_client.HTTP_requests(server='http://'+DV.DeviceIP)    
        status=HTTPrequest.request_datagram(DeviceCode=DV.DeviceCode,DatagramId=DG.Identifier) 
    NextUpdate=DV.getNextUpdate(jobID=jobID) 
    DV.updatePollingStatus(LastUpdated=status['LastUpdated'],Error=status['Error'],NextUpdate=NextUpdate)

class DeviceModel(models.Model):
    
    STATE_CHOICES=(
        (0,'STOPPED'),
        (1,'RUNNING')
    )
    
    __original_DeviceName = None
    __DeviceTypeCode = None
    DeviceName = models.CharField(max_length=50,unique=True,error_messages={'unique':_("Invalid device name - This name already exists in the DB.")})
    IO = models.OneToOneField(IOmodel,on_delete=models.CASCADE,related_name='pin2device',unique=True,null=True,blank=True)
    DeviceCode = models.IntegerField(unique=True,blank=True,null=True,error_messages={'unique':_("Invalid device code - This code already exists in the DB.")})
    DeviceIP = models.GenericIPAddressField(protocol='IPv4', unique=True,blank=True,null=True,error_messages={'unique':_("Invalid IP - This IP already exists in the DB.")})
    Type = models.ForeignKey(DeviceTypeModel,related_name="deviceType",on_delete=models.CASCADE)#limit_choices_to={'Connection': 'LOCAL'}
    DeviceState= models.PositiveSmallIntegerField(choices=STATE_CHOICES, default=0)
    Sampletime=models.PositiveIntegerField(default=600)
    RTsampletime=models.PositiveIntegerField(default=60)
    LastUpdated= models.DateTimeField(blank = True,null=True)
    NextUpdate= models.DateTimeField(blank = True,null=True)
    Connected = models.BooleanField(default=False)  # defines if the device is properly detected and transmits OK
    CustomLabels = models.CharField(max_length=1500,default='',blank=True) # json string containing the user-defined labels for each of the items in the datagrams
    Error= models.CharField(max_length=100,default='',blank=True)
    
    def _deviceType2Binding(self):
        '''THIS IS TO SEND ON THE DTATABINDING SOCKET THE CODE OF THE DEVICE TYPE. ON DEFAULT, IT SENDS THE pk '''
        return self.__DeviceTypeCode
    devicetype2str=property(_deviceType2Binding)
    
    def clean(self):
        if self.IO!=None:
            if self.IO.direction!='SENS':
                raise ValidationError(_('The GPIO selected is not configured as sensor'))
        if self.Sampletime<self.Type.MinSampletime or self.RTsampletime<self.Type.MinSampletime:
            raise ValidationError(_('The sample time selected is too low for the '+self.Type.Code+' sensors. It should be greater than '+str(self.Type.MinSampletime)+' sec.'))
        
    def __str__(self):
        return self.DeviceName
    
    def __init__(self, *args, **kwargs):
        super(DeviceModel, self).__init__(*args, **kwargs)
        self.__original_DeviceName = self.DeviceName
        
    def save(self, *args, **kwargs):
        if self.DeviceName != self.__original_DeviceName and self.__original_DeviceName != '':
            logger.info('Ha cambiado el nombre del dispositivo ' +self.__original_DeviceName+'. Ahora se llama ' + self.DeviceName)
            text=str(_('The name for the device ')) +self.__original_DeviceName+str(_(' has changed. Now it is named ')) + self.DeviceName
            PublishEvent(Severity=0,Text=text)
            #LocalDevices.signals.DeviceName_changed.send(sender=None, OldDeviceName=self.__original_DeviceName,NewDeviceName=self.DeviceName)
        self.__original_DeviceName = self.DeviceName
        self.__DeviceTypeCode=self.Type.Code
        super(DeviceModel, self).save(*args, **kwargs)
    
    def getScheduler(self):
        scheduler = BackgroundScheduler()
        url = 'sqlite:///scheduler.sqlite'
        scheduler.add_jobstore('sqlalchemy', url=url)
        return scheduler
        
    def stopPolling(self):
        if self.DeviceState==1:
            self.DeviceState=0
            self.save()
        self.update_requests()
    
    def startPolling(self):
        if self.DeviceState==0:
            self.DeviceState=1
            self.save()
        self.update_requests()
    
    def togglePolling(self):
        if self.DeviceState==0:
            self.startPolling()
        else:
            self.stopPolling()
            
    def getPollingJobIDs(self):
        DGs=Devices.models.DatagramModel.objects.filter(DeviceType=self.Type)
        jobIDs=[]
        if DGs != []:
            for DG in DGs:
                if DG.isSynchronous():
                    jobIDs.append({'id':self.DeviceName + '-' + DG.Identifier,'DG':DG})
        return jobIDs
    
    def update_requests(self,sched=None):
        
        if sched==None:
            scheduler=self.getScheduler()
        else:
            scheduler=sched
        
        try:
            scheduler.start()
        except:
            pass
        jobIDs=self.getPollingJobIDs()
        
        process=os.getpid()
        #logger.info("Enters update_requests on process " + str(process))
        
        if self.DeviceState==1:
            if jobIDs != []:
                for job in jobIDs:      
                    id=job['id']
                    DG=job['DG']
                    JOB=scheduler.get_job(job_id=id)
                    if JOB==None:     
                        callback="Devices.models:request_callback"
                        if self.Type.Connection=='LOCAL': 
                            scheduler.add_job(func=callback,trigger='interval',id=id,args=(self,DG,id),seconds=self.Sampletime,replace_existing=True,max_instances=1,coalesce=True,misfire_grace_time=30)
                        elif self.Type.Connection=='REMOTE':   
                            scheduler.add_job(func=callback,trigger='interval',id=id,args=(self, DG, id),seconds=self.Sampletime,replace_existing=True,max_instances=1,coalesce=True,misfire_grace_time=30)
                        elif self.Type.Connection=='MEMORY':
                            kwargs={'datagram':DG.Identifier}
                            scheduler.add_job(func=callback,trigger='interval',id=id,args=(self,DG,id), kwargs=kwargs,seconds=self.Sampletime,replace_existing=True,max_instances=1,coalesce=True,misfire_grace_time=30)
                        JOB=scheduler.get_job(job_id=id)
                        if JOB!=None: 
                            text=str(_('Polling for the device '))+self.DeviceName+str(_(' is started with sampletime= ')) + str(self.Sampletime) + str(_(' [s]. Next request at ') + str(JOB.next_run_time))
                            PublishEvent(Severity=0,Text=text,Persistent=True)
                        else:
                            PublishEvent(Severity=4,Text='Error adding job '+id+ ' to scheduler. Polling for device ' +self.DeviceName+' could not be started' ,Persistent=True)
                            self.DeviceState=0
                            self.save()
                    else:
                        PublishEvent(Severity=0,Text='Requests '+id+ ' already was in the scheduler. ' + str(_('Next request at ') + str(JOB.next_run_time)),Persistent=True)
            else:        
                self.DeviceState=0
                self.save()
                text=str(_('Polling for device '))+self.DeviceName+str(_(' could not be started. It has no Datagrams defined '))
                PublishEvent(Severity=3,Text=text,Persistent=True)
        else:
            if jobIDs != []:
                for job in jobIDs:
                    id=job['id']
                    JOB=scheduler.get_job(job_id=id)
                    if JOB!=None: 
                        scheduler.remove_job(id)
                        JOBs=scheduler.get_jobs()
                        if JOB in JOBs:
                            self.DeviceState=1
                            self.save()
                            text='Polling for the device '+self.DeviceName+' could not be stopped '
                            severity=5
                        else:
                            text='Polling for the device '+self.DeviceName+' is stopped ' 
                            severity=0
                    else:
                        text=str(_('Requests DB mismatch. Job ')) + str(id) + str(_(' did not exist.')) 
                        severity=5  
            else:
                text='Unhandled error on update_requests for device ' + str(self.DeviceName) 
                severity=5  
                
            PublishEvent(Severity=severity,Text=text,Persistent=True)
        
        if sched==None:
            scheduler.shutdown()
    
    def updatePollingStatus(self,LastUpdated,Error,NextUpdate):
        updateFields=['Error']
        if NextUpdate != None:
            self.NextUpdate=NextUpdate
            updateFields.append('NextUpdate')
        if LastUpdated!= None:
            self.LastUpdated=LastUpdated
            updateFields.append('LastUpdated')
            PublishEvent(Severity=0,Text=self.DeviceName+str(_(' updated OK')),Persistent=True)
        self.Error=Error
        if Error!='':
            PublishEvent(Severity=3,Text=self.DeviceName+' '+Error,Persistent=True)
            
        self.save(update_fields=updateFields)
        
        if 'LastUpdated' in updateFields:
            self.updateAutomationVars()
        
    def setLastUpdated(self,newValue):
        self.LastUpdated=newValue
        self.save(update_fields=['LastUpdated','Error','NextUpdate'])
    
    def getNextUpdate(self,jobID):
        if jobID!=None:
            scheduler=self.getScheduler()
            #scheduler.start()
            JOB=scheduler.get_job(job_id=jobID)
            #scheduler.shutdown()
            if JOB!=None:
                return JOB.next_run_time
        return None
            
    def setNextUpdate(self,jobID):
        next_run_time=getNextUpdate(jobID=jobID)
        self.NextUpdate=next_run_time
        if next_run_time==None:
            PublishEvent(Severity=3,Text='Next run time for job '+jobID+ ' could not be fetched.',Persistent=True)
        self.save(update_fields=['NextUpdate',])
        
        
    def updateCustomLabels(self):
        DGs=Devices.models.DatagramModel.objects.filter(DeviceType=self.Type)
        if self.CustomLabels!='':
            CustomLabels=json.loads(self.CustomLabels)
            for DG in DGs:
                datagram=DG.getStructure()
                names=datagram['names']
                for name in names:
                    if not name in CustomLabels[DG.Identifier]:
                        CustomLabels[DG.Identifier][name]=''
            self.CustomLabels=json.dumps(CustomLabels)
            self.save()
        else:
            return
    
    def getRegistersTables(self,DG=None):
        if DG==None:
            DGs=Devices.models.DatagramModel.objects.filter(DeviceType=self.Type)
            tables=[]
            if len(DGs)>0:
                for DG in DGs:
                    tables.append(str(self.pk)+'_'+str(DG.pk))
        else:
            tables=str(self.pk)+'_'+str(DG.pk)
        return tables
    
    def getLatestData(self):
        DGs=Devices.models.DatagramModel.objects.filter(DeviceType=self.Type)
        if self.CustomLabels!='':
            CustomLabels=json.loads(self.CustomLabels)
        else:
            CustomLabels=None
        
        Data={}
        if len(DGs)>0 and CustomLabels!=None:
            applicationDBs=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                      configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH) 
            
            for DG in DGs:
                table=self.getRegistersTables(DG=DG)
                vars=''
                for name in CustomLabels[DG.Identifier]:
                    vars+=',"'+name+'"'
                sql='SELECT '+vars[1:]+' FROM "'+ table +'" ORDER BY timestamp DESC LIMIT 1'
                row=applicationDBs.registersDB.retrieve_from_table(sql=sql,single=True,values=(None,))
                if row != None:
                    for i,name in enumerate(CustomLabels[DG.Identifier]):
                        Data[CustomLabels[DG.Identifier][name]]=row[i]
                else:
                    for name in CustomLabels[DG.Identifier]:
                        Data[CustomLabels[DG.Identifier][name]]=None
        else:
            Data=None
        #print(Data)
        return Data
        
    def getDeviceVariables(self):
        DeviceVars=[]
        DGs=Devices.models.DatagramModel.objects.filter(DeviceType=self.Type)
        if self.CustomLabels!='':
            CustomLabels=json.loads(self.CustomLabels)
        else:
            CustomLabels=None
            
        for DG in DGs:
            datagram=DG.getStructure()
            Vars=datagram['names']
            Types=datagram['types']
            table=self.getRegistersTables(DG=DG)
            if CustomLabels!=None:
                CustomVars=CustomLabels[DG.Identifier]
            else:
                CustomVars={}
                for name in datagram['names']:
                    CustomVars[name]=name
                
            for var,type in zip(Vars,Types):
                if type=='digital':
                    BitLabels=CustomVars[var].split('$')
                    for i,bitLabel in enumerate(BitLabels):
                        DeviceVars.append({'Label':bitLabel,'Tag':var,'Device':self.pk,'Table':table,'BitPos':i,'Sample':datagram['sample']*self.Sampletime})
                else:
                    DeviceVars.append({'Label':CustomVars[var],'Tag':var,'Device':self.pk,'Table':table,'BitPos':None,'Sample':datagram['sample']*self.Sampletime})
        return DeviceVars
    
    def updateAutomationVars(self):
        AutomationVars=HomeAutomation.models.AutomationVariablesModel.objects.filter(Device=self.pk)
        DeviceVars=self.getDeviceVariables()
        for dvar in DeviceVars:
            try:
                avar=AutomationVars.get(Tag=dvar['Tag'],Table=dvar['Table'],Device=dvar['Device'],BitPos=dvar['BitPos'])
            except:
                avar=None
                
            if avar==None:
                avar=HomeAutomation.models.AutomationVariablesModel()
                avar.create(Label=dvar['Label'],Tag=dvar['Tag'],Device=dvar['Device'],Table=dvar['Table'],BitPos=dvar['BitPos'],Sample=dvar['Sample'])
            
            avar.executeAutomationRules()
            
    def deleteAutomationVars(self):
        HomeAutomation.models.AutomationVariablesModel.objects.filter(Device=self.pk).delete()
            
    class Meta:
        permissions = (
            ("view_devices", "Can see available devices"),
            ("change_state", "Can change the state of the devices"),
            ("add_device", "Can add new devices to the installation")
        )
        verbose_name = _('Slave device')
        verbose_name_plural = _('Slave devices')
        
@receiver(post_save, sender=DeviceModel, dispatch_uid="update_DeviceModel")
def update_DeviceModel(sender, instance, update_fields,**kwargs):
    if kwargs['created']:   # new instance is created
        registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                           configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')
        registerDB.create_DeviceRegistersTables(DV=instance)
        instance.update_requests()
    
    if update_fields!=None and 'LastUpdated' in update_fields:
        pass
        #instance.updateAutomationVars()
               
@receiver(post_delete, sender=DeviceModel, dispatch_uid="delete_DeviceModel")
def delete_DeviceModel(sender, instance,**kwargs):
    instance.deleteAutomationVars()
    logger.info('Se ha eliminado el dispositivo ' + str(instance))

class DeviceModelBinding(WebsocketBindingWithMembers):

    model = DeviceModel
    stream = "Device_params"
    fields = ["DeviceName","IO","DeviceCode","DeviceIP","Type","Sampletime","DeviceState","LastUpdated","Error","devicetype2str"]

    @classmethod
    def group_names(cls, *args, **kwargs):
        return ["Device-models",]

    def has_permission(self, user, action, pk):
        return True
        
    
class ReportModelManager(models.Manager):
    def create_Report(self, ReportTitle,Periodicity,DataAggregation,ReportContentJSON):
        Rep = self.create(ReportTitle=ReportTitle,Periodicity=Periodicity,DataAggregation=DataAggregation,ReportContentJSON=ReportContentJSON)
        Rep.save()
        
class ReportModel(models.Model):
    PERIODICITY_CHOICES=(
        (2,_('Every day')),
        (3,_('Every week')),
        (4,_('Every month'))
    )
    AGGREGATION_CHOICES=(
        (0,_('No aggregation')),
        (1,_('Hourly')),
        (2,_('Daily')),
        (4,_('Monthly'))
    )
    ReportTitle = models.CharField(max_length=50,unique=True,error_messages={'unique':_("Invalid report title - This title already exists in the DB.")})
    Periodicity= models.PositiveSmallIntegerField(help_text=_('How often the report will be generated'),choices=PERIODICITY_CHOICES)
    DataAggregation= models.PositiveSmallIntegerField(help_text=_('Data directly from the DB or averaged over a period'),choices=AGGREGATION_CHOICES)
    ReportContentJSON=models.CharField(help_text='Content of the report in JSON format', max_length=20000)
    
    objects = ReportModelManager()
    
    def checkTrigger(self):
        import datetime
        now=datetime.datetime.now()
        if now.hour==0 and now.minute==0:
            if self.Periodicity==2: # daily report launched on next day at 00:00
                return True
            elif self.Periodicity==3 and now.weekday()==0: # weekly report launched on Monday at 00:00
                return True
            elif self.Periodicity==4 and now.day==1: # monthly report launched on 1st day at 00:00
                return True
        return False
    
    def getReportData(self,toDate=None):
        from Devices.Reports import get_report
        import datetime
        if self.Periodicity==2: # daily report
            offset=datetime.timedelta(hours=24)
        elif self.Periodicity==3: # weekly report
            offset=datetime.timedelta(weeks=1)
        elif self.Periodicity==4: # monthly report
            if toDate==None:
                now=datetime.datetime.now()
            else:
                now=toDate
            days=calendar.monthrange(now.year, now.month)[1]
            offset=datetime.timedelta(hours=days*24)
        if toDate==None:
            toDate=timezone.now() 
        fromDate=toDate-offset
        toDate=toDate-datetime.timedelta(minutes=1)
        reportData=get_report(reporttitle=self.ReportTitle,fromDate=fromDate,toDate=toDate,aggregation=self.DataAggregation)
        return reportData,fromDate,toDate
        #reportData= {'reportTitle': 'Prueba1', 'fromDate': datetime.datetime(2017, 8, 30, 9, 14, 38), 'toDate': datetime.datetime(2017, 8, 31, 2, 0), 
        # 'charts': [{'chart_title': 'Temperatura', 'cols': [{'table': 'Ambiente en salon_data', 'name': 'Temperature_degC', 'label': 'Temperature_degC', 'type': 'number', 'bitPos': None}, {'table': 'Ambiente en salon_data', 'name': 'Heat Index_degC', 'label': 'Heat Index_degC', 'type': 'number', 'bitPos': None}], 'rows': {'x_axis': [{'v': 'Date(2017,7,30,9,30,0)'}, {'v': 'Date(2017,7,30,10,30,0)'}, {'v': 'Date(2017,7,30,11,30,0)'}, {'v': 'Date(2017,7,30,12,30,0)'}, {'v': 'Date(2017,7,30,13,30,0)'}, {'v': 'Date(2017,7,30,14,30,0)'}, {'v': 'Date(2017,7,30,15,30,0)'}, {'v': 'Date(2017,7,30,16,30,0)'}, {'v': 'Date(2017,7,30,17,30,0)'}, {'v': 'Date(2017,7,30,18,30,0)'}, {'v': 'Date(2017,7,30,19,30,0)'}, {'v': 'Date(2017,7,30,20,30,0)'}, {'v': 'Date(2017,7,30,21,30,0)'}, {'v': 'Date(2017,7,30,22,30,0)'}, {'v': 'Date(2017,7,30,23,30,0)'}, {'v': 'Date(2017,7,31,0,30,0)'}, {'v': 'Date(2017,7,31,1,30,0)'}], 'y_axis': [[26.6, 0.0], [26.916666666666664, 0.0], [27.0, 0.0], [27.02777777777778, 0.0], [27.12121212121212, 0.0], [27.44827586206896, 0.0], [28.0, 0.0], [28.0, 0.0], [28.0, 0.0], [28.0, 0.0], [28.0, 0.0], [27.583333333333332, 0.0], [27.138888888888893, 0.0], [27.055555555555557, 0.0], [27.138888888888893, 0.0], [27.0, 0.0], [27.0, 0.0]]}}, 
        #           {'chart_title': 'Humedad', 'cols': [{'table': 'Ambiente en salon_data', 'name': 'RH_pc', 'label': 'RH_pc', 'type': 'number', 'bitPos': None}], 'rows': {'x_axis': [{'v': 'Date(2017,7,30,9,30,0)'}, {'v': 'Date(2017,7,30,10,30,0)'}, {'v': 'Date(2017,7,30,11,30,0)'}, {'v': 'Date(2017,7,30,12,30,0)'}, {'v': 'Date(2017,7,30,13,30,0)'}, {'v': 'Date(2017,7,30,14,30,0)'}, {'v': 'Date(2017,7,30,15,30,0)'}, {'v': 'Date(2017,7,30,16,30,0)'}, {'v': 'Date(2017,7,30,17,30,0)'}, {'v': 'Date(2017,7,30,18,30,0)'}, {'v': 'Date(2017,7,30,19,30,0)'}, {'v': 'Date(2017,7,30,20,30,0)'}, {'v': 'Date(2017,7,30,21,30,0)'}, {'v': 'Date(2017,7,30,22,30,0)'}, {'v': 'Date(2017,7,30,23,30,0)'}, {'v': 'Date(2017,7,31,0,30,0)'}, {'v': 'Date(2017,7,31,1,30,0)'}], 'y_axis': [[29.4], [29.083333333333336], [29.0], [29.027777777777782], [29.0], [29.0], [29.0], [29.0], [29.0], [29.0], [29.0], [29.0], [29.0], [29.0], [29.027777777777782], [29.0], [29.0]]}}]}
    
    def generate(self):
        ReportData,fromDate,toDate=self.getReportData()                   
        RITM=ReportItems(Report=self,fromDate=fromDate,toDate=toDate,data='')
        RITM.save()
        
    def __str__(self):
        return self.ReportTitle
        
    class Meta:
        permissions = (
            ("add_report", "Can configure and add reports"),
            ("view_report", "Can view reports configured"),
            ("view_plots", "Can see the historic plots from any device")
        )
        verbose_name = _('Report')
        verbose_name_plural = _('Reports')

def path_reportfile_name(instance, filename):
    import os
    from django.conf import settings
    filename, file_extension = os.path.splitext(filename)
    return os.path.join(settings.MEDIA_ROOT,'Reports',instance.Report.ReportTitle+'_'+str(instance.fromDate).split('+')[0].split('.')[0]+'-'+str(instance.toDate).split('+')[0].split('.')[0] +file_extension)

class ReportItems(models.Model):
    Report = models.ForeignKey(ReportModel, on_delete=models.CASCADE)
    fromDate = models.DateTimeField(blank = True,editable=False,null=True)
    toDate = models.DateTimeField(blank = True,editable=False,null=True)
    data = models.CharField(help_text='Data of the report in JSON format', max_length=20000,null=True,blank=True)
    
    def __str__(self):
        return str(self.Report.ReportTitle)
        
    class Meta:
        unique_together = ('Report', 'fromDate','toDate')
        verbose_name = _('Generated report')
        verbose_name_plural = _('Generated reports')
        ordering = ('fromDate',)
        
        
class DatagramItemModel(models.Model):
    DATATYPE_CHOICES=(
        ('INTEGER',_('Analog Integer')),
        ('FLOAT',_('Analog Float')),
        ('DIGITAL',_('Digital')),
    )
    PLOTTYPE_CHOICES=(
        ('line',_('Hard Line')),
        ('spline',_('Smoothed Line')),
        ('column',_('Bars')),
        ('area',_('Area')),
    )
    HumanTag = models.CharField(max_length=20,unique=True)
    DataType= models.CharField(max_length=10,choices=DATATYPE_CHOICES)
    PlotType= models.CharField(max_length=10,choices=PLOTTYPE_CHOICES,default='spline')
    Units = models.CharField(max_length=10,null=True,blank=True)
    
    def clean(self):
        if self.DataType=='DIGITAL':
            self.Units='bits'
            self.PlotType='line'
                        
    def __str__(self):
        return self.HumanTag
    
    def getHumanName(self):
        return self.HumanTag+'_'+self.Units
    
    class Meta:
        verbose_name = _('Datagram item')
        verbose_name_plural = _('Datagram items')
        
class DatagramModel(models.Model):
    DATAGRAMTYPE_CHOICES=(
        ('Synchronous','Synchronous'),
        ('Asynchronous','Asynchronous')
    )
    Identifier = models.CharField(max_length=20)
    Code= models.PositiveSmallIntegerField(help_text='Identifier byte-type code')
    Type= models.CharField(max_length=12,choices=DATAGRAMTYPE_CHOICES)
    DeviceType = models.ForeignKey(DeviceTypeModel,on_delete=models.CASCADE)
    Items = models.ManyToManyField(DatagramItemModel, through='ItemOrdering')#
    def __str__(self):
        return self.Identifier
    
    def clean(self):
        pass
        
    def isSynchronous(self):
        return int(self.Type=='Synchronous')
    
    def getDBTypes(self):
        types=[]
        for item in self.itemordering_set.all():
            if item.Item.DataType!= 'DIGITAL':
                types.insert(item.order-1,'analog')
            else:
                types.insert(item.order-1,'digital')
        types.insert(0,'datetime')
        return types
    
    def getStructure(self):
        """RETURNS THE STRUCTURE OF A DATAGRAM ASSIGNING THE FOLLOWING NAMES TO THE VARIABLES (COLUMNS IN THE DB)
        THE COLUMN NAME IS THE CONCATENATION OF THE VARIABLE PK + '_'+ NUMBER. THE NUMBER IS A CORRELATIVE NUMBER BETWEEN 1 AND THE NUMBER OF REPETITIONS OF 
        THE VARIABLE IN THE DATAGRAM
        """
        names=[]
        types=[]
        datatypes=[]
        units=[]
        plottypes=[]
        datagramID=self.Identifier
        checkedPK={}
        for item in self.itemordering_set.all().order_by('order'):
            numItems=1
            if not str(item.Item.pk) in checkedPK:
                checkedPK[str(item.Item.pk)]=1
            else:
                numItems=checkedPK[str(item.Item.pk)]+1
                checkedPK[str(item.Item.pk)]+=1
            names.insert(item.order-1,str(item.Item.pk)+'_'+str(numItems)+'_'+str(self.pk))
            units.insert(item.order-1,item.Item.Units)
            plottypes.insert(item.order-1,item.Item.PlotType)
            if item.Item.DataType!= 'DIGITAL':
                types.insert(item.order-1,'analog')
                datatypes.insert(item.order-1,item.Item.DataType)
            else:
                types.insert(item.order-1,'digital')
                datatypes.insert(item.order-1,'INTEGER')
        if self.isSynchronous():
            sample=1
        else:
            sample=0
        
        return {'pk':self.pk,'ID':datagramID,'names':names,'types':types,'datatypes':datatypes,'units':units,'plottypes':plottypes,'sample':sample}

    class Meta:
        verbose_name = _('Datagram')
        verbose_name_plural = _('Datagrams')
        unique_together = (('DeviceType', 'Identifier'),('DeviceType', 'Code'))
       
@receiver(post_save, sender=DatagramModel, dispatch_uid="update_DatagramModel")
def update_DatagramModel(sender, instance, update_fields,**kwargs):
    if not kwargs['created']:   # an instance has been modified
        logger.info('Se ha modificado el datagram ' + str(instance.DeviceType)+"_"+str(instance))
        DVs=DeviceModel.objects.filter(Type=instance.DeviceType)
        if len(DVs)>0:
            registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                           configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')
            for DV in DVs:
                DV.updateAutomationVars()
                table=DV.getRegistersTables(DG=instance)
                registerDB.check_columns_registersDB(table=table,datagramStructure=instance.getStructure())
                
    else:
        logger.info('Se ha creado el datagram ' + str(instance.DeviceType)+"_"+str(instance))
        logger.info('Tiene ' + str(instance.Items.count())+' ' + (DatagramItemModel._meta.verbose_name.title() if (instance.Items.count()==1) else DatagramItemModel._meta.verbose_name_plural.title()))
        for item in instance.Items.all():
            logger.info('   - ' + str(item.HumanTag))

def getAllVariables():

    info=[]
    DVs=Devices.models.DeviceModel.objects.all()
    IOs=IOmodel.objects.all()
    MainVars=HomeAutomation.models.MainDeviceVarModel.objects.all()
    tempvars=[]
    if len(IOs)>0:
        for IO in IOs:
            if IO.direction=='IN' or IO.direction=='OUT':
                if IO.direction=='IN':
                    table='inputs'
                else:
                    table='outputs'
                tempvars.append({'device':'Main','table':table,'tag':str(IO.pin),
                                'label':[IO.label,],'extrapolate':'keepPrevious','type':'digital','plottype':'line'})# this is to tell the template that it is a boolean value
                                
        info.append({'deviceName':'Main','variables':tempvars})
    tempvars=[]
    if len(MainVars)>0:
        for VAR in MainVars:
            table='MainVariables'
            tempvars.append({'device':'Main','table':table,'tag':str(VAR.pk),
                            'label':VAR.Label,'extrapolate':'keepPrevious','type':'analog','plottype':VAR.PlotType})
                                
        info.append({'deviceName':'Main','variables':tempvars})
        
    for DV in DVs:    # device[0]= DeviceName, device[1]=DeviceType  
        DGs=Devices.models.DatagramModel.objects.filter(DeviceType=DV.Type)#XMLParser.getDatagramsStructureForDeviceType(deviceType=DEVICE_TYPE)
        tempvars=[]
        for DG in DGs: 
            table=DV.getRegistersTables(DG=DG)  #str(DV.pk)+'_'+str(DG.pk)
            Labeliterable=[]
            datagram=DG.getStructure()
            if DV.CustomLabels!='':
                CustomLabels=json.loads(DV.CustomLabels)
                labels=CustomLabels[DG.Identifier]
                for name in datagram['names']:
                    Labeliterable.append(labels[name])
            else:
                for name in datagram['names']:
                    IT=Devices.models.DatagramItemModel.objects.get(pk=int(name.split('_')[0]))
                    Labeliterable.append(IT.getHumanName())
            for i,var in enumerate(Labeliterable):                     
                CustomLabel='' 
                type=datagram['types'][i]
                if type=='digital':                                                          
                    if str(var).find('$')>=0:
                        try:
                            CustomLabel=str(var).split('$')
                        except:
                            CustomLabel=''
                else:
                    CustomLabel=var.replace('_',' [')+']'
                if (str(var).lower()!='spare') and (str(var).lower()!='timestamp'):                                       
                    tempvars.append({'device':DV.DeviceName,'table':table,'tag':datagram['names'][i],'type':type,'label':CustomLabel,
                                    'plottype':datagram['plottypes'][i],'extrapolate':''})
        info.append({'deviceName':DV.DeviceName,'variables':tempvars})
    return info
    
class ItemOrdering(models.Model):
    datagram = models.ForeignKey(DatagramModel, on_delete=models.CASCADE)
    Item = models.ForeignKey(DatagramItemModel, on_delete=models.CASCADE,blank=True,null=True)
    order = models.PositiveSmallIntegerField(help_text='Position in the dataframe 1-based')
    
    def __str__(self):
        return str(self.datagram) + ':' +str(self.order)
        
    class Meta:
        verbose_name = _('Item')
        verbose_name_plural = _('Items')
        ordering = ('order',)
        

# these Signal functions are not triggered due to a Django bug https://code.djangoproject.com/ticket/16073
# def AnItems_changed(sender,instance, action, **kwargs):
#     logger.info('Ahora tiene ' + str(instance.AnItems.count())+' ' + (AnalogItemModel._meta.verbose_name.title() if (instance.AnItems.count()==1) else AnalogItemModel._meta.verbose_name_plural.title()))
#     for analog in instance.AnItems.all():
#         logger.info('   - ' + str(analog.HumanTag))
#     
# def DgItems_changed(sebder,instance, action,**kwargs):
#     logger.info('Ahora tiene ' + str(instance.DgItems.count())+' ' + (DigitalItemModel._meta.verbose_name.title() if (instance.DgItems.count()==1) else DigitalItemModel._meta.verbose_name_plural.title()))
#     for digital in instance.DgItems.all():
#         logger.info('   - ' + str(digital.HumanTag))
# m2m_changed.connect(AnItems_changed, sender=DatagramModel.AnItems.through,weak=False)
# m2m_changed.connect(DgItems_changed, sender=DatagramModel.DgItems.through,weak=False)

class CommandModel(models.Model):
    DeviceType = models.ForeignKey(DeviceTypeModel,on_delete=models.CASCADE)
    Identifier = models.CharField(max_length=10)
    HumanTag = models.CharField(max_length=50)
    
    def __str__(self):
        return self.HumanTag
        
    class Meta:
        verbose_name = _('Command')
        verbose_name_plural = _('Commands')
        unique_together = ('DeviceType', 'Identifier',)