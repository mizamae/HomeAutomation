import os
import sys
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.db.models.signals import post_save,post_delete,pre_delete
from django.db.models.signals import m2m_changed

import datetime

import RPi.GPIO as GPIO

from channels.binding.websockets import WebsocketBinding,WebsocketBindingWithMembers 

from Events.consumers import PublishEvent

import HomeAutomation.models
import json
import itertools
import utils.BBDD
from HomeAutomation.constants import REGISTERS_DB_PATH
from .constants import CONNECTION_CHOICES,LOCAL_CONNECTION,REMOTE_TCP_CONNECTION,MEMORY_CONNECTION,\
                        STATE_CHOICES,DEVICES_PROTOCOL,DEVICES_SUBNET,DEVICES_SCAN_IP4BYTE,\
                        DEVICES_CONFIG_FILE,IP_OFFSET,POLLING_SCHEDULER_URL,\
                        STOPPED_STATE,RUNNING_STATE,\
                        DATAGRAMTYPE_CHOICES,DATATYPE_CHOICES,PLOTTYPE_CHOICES,LINE_PLOT,SPLINE_PLOT,DG_SYNCHRONOUS,\
                        DTYPE_DIGITAL,DTYPE_INTEGER,\
                        GPIO_DIRECTION_CHOICES,GPIO_OUTPUT,GPIO_INPUT,GPIO_SENSOR,GPIOVALUE_CHOICES,GPIO_HIGH,GPIO_LOW
                        
from .apps import DevicesAppException

import logging
from blaze.tests.test_sql import sql

logger = logging.getLogger("project")


#set up GPIO using BCM numbering
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
    
class MasterGPIOs(models.Model):
    
    class Meta:
        verbose_name = _('Input/Output')
        verbose_name_plural = _('Inputs/Outputs')
        permissions = (
            ("view_mastergpios", "Can see available gpios"),
            ("change_state_mastergpios", "Can change the state of the GPIOs"),
        )
    SQLcreateRegisterTable = ''' 
                                CREATE TABLE IF NOT EXISTS $ (
                                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    *
                                    UNIQUE (timestamp)                    
                                ); 
                                '''  # the * will be replaced by the column names and $ by inputs or outputs
    SQLinsertRegister = ''' INSERT INTO %s(*) VALUES(?) ''' # the * will be replaced by the column names and the ? by the values 
    
    Pin = models.PositiveSmallIntegerField(primary_key=True,unique=True,help_text=str(_('The number of the pin following BCM notation.')))
    Label = models.CharField(max_length=50,unique=True,help_text=str(_('Label describing the GPIO functional meaning.')))
    Direction = models.PositiveSmallIntegerField(choices=GPIO_DIRECTION_CHOICES,help_text=str(_('Choose wether the GPIO is to be an output, an input or a sensor interface.')))
    Value = models.PositiveSmallIntegerField(default=0,choices=GPIOVALUE_CHOICES,help_text=str(_('Set the value of the GPIO (only applies to outputs)')))
    
    def __init__(self, *args, **kwargs):
        super(MasterGPIOs, self).__init__(*args, **kwargs)
    
    def store2DB(self):
        self.full_clean()
        super().save() 
        
    def setHigh(self):
        if self.Direction==GPIO_OUTPUT:
            GPIO.setup(int(self.Pin), GPIO.OUT)
            GPIO.output(int(self.Pin),GPIO.HIGH)
            newValue=GPIO.HIGH
            self.update_value(newValue=newValue,timestamp=None,writeDB=True,force=False)
            
    def setLow(self):
        if self.Direction==GPIO_OUTPUT:
            GPIO.setup(int(self.Pin), GPIO.OUT)
            GPIO.output(int(self.Pin),GPIO.LOW)
            newValue=GPIO.LOW
            self.update_value(newValue=newValue,timestamp=None,writeDB=True,force=False)
            
    def toggle(self):
        if self.Value==GPIO.HIGH:
            self.setLow()
        else:
            self.setHigh()
    
    def getLatestData(self):
        Data={}
        name=self.getRegistersDBTag()
        Data[name]={}
        table=self.getRegistersDBTableName()
        vars='"timestamp","'+name+'"'
        sql='SELECT '+vars+' FROM "'+ table +'" ORDER BY timestamp DESC LIMIT 1'
        from utils.BBDD import getRegistersDBInstance
        DB=getRegistersDBInstance()
        row=DB.executeTransaction(SQLstatement=sql)
        if row != []:
            row=row[0]
            timestamp=row[0]
            row=row[1]
        else:
            timestamp=None
            row=None
        Data[name]['timestamp']=timestamp
        Data[name]['value']=row
        return Data
    
    def update_value(self,newValue,timestamp=None,writeDB=True,force=False):
        if newValue!=self.Value or force:
            if writeDB:
                now=timezone.now()
                if timestamp==None:
                    self.insertRegister(TimeStamp=now-datetime.timedelta(seconds=1))
                
            if newValue!=self.Value:
                text=str(_('The value of the GPIO "')) +self.Label+str(_('" has changed. Now it is ')) + str(newValue)
                PublishEvent(Severity=0,Text=text)
                self.Value=newValue
                self.save(update_fields=['Value'])
            
            if writeDB :
                if timestamp==None:
                    self.insertRegister(TimeStamp=now)
                else:
                    self.insertRegister(TimeStamp=timestamp)
                
            if self.Direction==GPIO_OUTPUT:
                GPIO.setup(int(self.Pin), GPIO.OUT)
                if self.Value==1:
                    GPIO.output(int(self.Pin),GPIO.HIGH)
                elif self.Value==0:
                    GPIO.output(int(self.Pin),GPIO.LOW)
                
            self.updateAutomationVars()
    
    def getRegistersDBTableName(self):
        if self.Direction==GPIO_INPUT:
            table='inputs'
        elif self.Direction==GPIO_OUTPUT:
            table='outputs'
        else:
            raise ValueError(_('Only GPIOs defined as Input or Output can be registered to the DB'))
        return table
    
    def getRegistersDBTag(self):
        return str(self.Pin)
    
    def getStructure(self):
        IOs=MasterGPIOs.objects.filter(Direction=self.Direction)
        values=[]
        names=[]
        types=[]
        datatypes=[]
        plottypes=[]
        pks=[]
        if IOs.count():
            for IO in IOs:
                pks.append(IO.pk)
                values.append(IO.Value)
                names.append(IO.getRegistersDBTag())
                types.append(DTYPE_INTEGER)
                datatypes.append('INTEGER')
                plottypes.append(LINE_PLOT)
        return {'pk':pks,'names':names,'values':values,'types':types,'datatypes':datatypes,'plottypes':plottypes}
        
    def _createRegistersTable(self,Database):
        """
        Creates the table corresponding to the GPIO Direction
        """
        TableName=self.getRegistersDBTableName()

        try:
            struct=self.getStructure()
            temp_string=''
            for i in range(0,len(struct['names'])):
                temp_string+='"'+struct['names'][i] + '" ' + struct['datatypes'][i] + ','
            sql=self.SQLcreateRegisterTable.replace('*',temp_string).replace('$','"'+TableName+'"')
            result=Database.executeTransactionWithCommit(SQLstatement=sql, arg=[])
            if result==0:
                logger.info('Succeded in creating the table "'+TableName+'"') 
        except:
            text = str(_("Error in create_GPIO_table: ")) + str(sys.exc_info()[1]) 
            raise DevicesAppException(text)
            PublishEvent(Severity=5,Text=text + 'SQL: ' + sql,Persistent=True)        
            
    def getInsertRegisterSQL(self):
        
        sql=self.SQLinsertRegister
        #SQLinsertRegister = ''' INSERT INTO %s(*) VALUES(?) '''   # the * will be replaced by the column names and the $ by the values  
        struct=self.getStructure()
        names=struct['names']
        values=[]
        valuesHolder='?,'
        columns='timestamp,'
        if len(names)>0:
            for i,name in enumerate(names):
                values.append(struct['values'][i])
                columns+='"'+name+'",'
                valuesHolder+='?,'
        columns=columns[:-1]
        valuesHolder=valuesHolder[:-1]
        sql=sql.replace('%s','"'+self.getRegistersDBTableName()+'"').replace('*',columns).replace('?',valuesHolder)
        return {'query':sql,'num_args':len(names),'values':values}
    
    def checkRegistersDB(self,Database):
        
        rows=Database.retrieve_DB_structure(fields='*')   #('table', 'devices', 'devices', 4, "CREATE TABLE devices...)
        
        required_DGs=[]

        found=False
        table_to_find=self.getRegistersDBTableName()
        for row in rows:
            if (row[1]==table_to_find):   # found the table in the DB
                found=True
                struct=self.getStructure()
                Database.checkTableColumns(table=table_to_find,desiredColumns={'names':struct['names'],'datatypes':struct['datatypes']})
                break
        if found is not True:
            self._createRegistersTable(Database=Database)
            logger.info('The table '+table_to_find+' was not created.')
            
    def insertRegister(self,TimeStamp,NULL=False):
        """
        INSERTS A REGISTER IN THE registersDB INTO THE APPROPIATE TABLE.
        """
        try:                              
            TimeStamp=TimeStamp.replace(microsecond=0)
            query=self.getInsertRegisterSQL()
            sql=query['query']
            num_args=query['num_args']
            values=query['values']
            if NULL==True:
                logger.info('Inserted NULL values on GPIO ' + self.Label)
                values=[]
                for i in range(0,num_args):  
                    values.append(None)
            values.insert(0,TimeStamp)
            from utils.BBDD import getRegistersDBInstance
            DB=getRegistersDBInstance(year=TimeStamp.year)
            self.checkRegistersDB(Database=DB)
            DB.executeTransactionWithCommit(SQLstatement=sql, arg=values)
        except:
            raise DevicesAppException("Unexpected error in insert_GPIO_register:" + str(sys.exc_info()[1]))
        
    def InputChangeEvent(self,*args):
        val=GPIO.input(self.Pin)
        newValue=int(val)
        self.update_value(newValue=newValue,timestamp=None,writeDB=True)
    
    def updateAutomationVars(self):
        table=self.getRegistersDBTableName()
        AutomationVars=HomeAutomation.models.AutomationVariablesModel.objects.filter(Device='Main')
        
        dvar={'Label':self.Label,'Tag':str(self.getRegistersDBTag()),'Device':'Main','Table':table,'BitPos':None,'Sample':0}
        try:
            avar=AutomationVars.get(Tag=dvar['Tag'],Table=dvar['Table'],BitPos=dvar['BitPos'])
        except:
            avar=None
            
        if avar==None:
            avar=HomeAutomation.models.AutomationVariablesModel()
            avar.create(Label=dvar['Label'],Tag=dvar['Tag'],Device=dvar['Device'],Table=dvar['Table'],BitPos=dvar['BitPos'],Sample=dvar['Sample'])
        
        avar.executeAutomationRules()
    
    def deleteAutomationVars(self):
        table=self.getRegistersDBTableName()
        try:
            avar=HomeAutomation.models.AutomationVariablesModel.objects.get(Device='Main',Tag=str(self.pk),Table=table)
            avar.delete()
        except:
            pass
        
    @staticmethod
    def getIOVariables(self):
        DeviceVars=[]
        IOs=MasterGPIOs.objects.filter(Q(Direction=GPIO_INPUT) | Q(Direction=GPIO_OUTPUT))
        for IO in IOs:
            DeviceVars.append({'Label':IO.Label,'Tag':IO.getRegistersDBTag(),'Device':'Main','Table':IO.getRegistersDBTableName(),'BitPos':None})
        return DeviceVars        
    
    @staticmethod
    def initializeIOs(declareInputEvent=True):
        IOs=MasterGPIOs.objects.all()
        logger.info("There are " + str(len(IOs))+" IOs configured")
        if len(IOs):
            logger.info("Initializing IOs from DB")
            for IO in IOs:
                if IO.Direction==GPIO_OUTPUT:
                    GPIO.setup(int(IO.Pin), GPIO.OUT)
                    GPIO.output(int(IO.Pin),IO.Value)
                    newValue=IO.Value
                    IO.update_value(newValue=newValue,timestamp=None,writeDB=True,force=True)
                    print("   - Initialized Output on pin " + str(IO.Pin))
                elif IO.Direction==GPIO_INPUT:
                    if declareInputEvent:
                        GPIO.setup(int(IO.Pin), GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
                        #GPIO.remove_event_detect(int(IO.Pin))
                        GPIO.add_event_detect(int(IO.Pin), GPIO.BOTH, callback=IO.InputChangeEvent, bouncetime=200)
                        IO.Value=GPIO.input(int(IO.Pin))
                        newValue=IO.Value
                        IO.update_value(newValue=newValue,timestamp=None,writeDB=True,force=True)
                    else:
                        GPIO.setup(int(IO.Pin), GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
                        #GPIO.remove_event_detect(int(IO.Pin))
    
                    print("   - Initialized Input on pin " + str(IO.Pin))
                    
    def __str__(self):
        return self.Label + ' on pin ' + str(self.Pin)
        
    

@receiver(post_save, sender=MasterGPIOs, dispatch_uid="update_MasterGPIOs")
def update_MasterGPIOs(sender, instance, update_fields,**kwargs):
    if kwargs['created']:   # new instance is created  
        logger.info('The IO ' + str(instance) + ' has been registered on the process ' + str(os.getpid()))
        if instance.Direction==GPIO_OUTPUT:
            GPIO.setup(int(instance.Pin), GPIO.OUT)
            if instance.Value==GPIO_HIGH:
                GPIO.output(int(instance.Pin),GPIO.HIGH)
            else:
                GPIO.output(int(instance.Pin),GPIO.LOW)
            logger.info("Initialized Output on pin " + str(instance.Pin))
        elif instance.Direction==GPIO_INPUT:
            GPIO.setup(int(instance.Pin), GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
            GPIO.remove_event_detect(int(instance.Pin))
            GPIO.add_event_detect(int(instance.Pin), GPIO.BOTH, callback=instance.InputChangeEvent, bouncetime=200)  
            logger.info("Initialized Input on pin " + str(instance.Pin))
    else:
        pass

@receiver(post_delete, sender=MasterGPIOs, dispatch_uid="delete_MasterGPIOs")
def delete_MasterGPIOs(sender, instance,**kwargs):
    instance.deleteAutomationVars()
    logger.info('Se ha eliminado la IO ' + str(instance))
        
class MasterGPIOsBinding(WebsocketBinding):

    model = MasterGPIOs
    stream = "GPIO_values"
    fields = ["Pin","Label","Direction","Value"]

    @classmethod
    def group_names(cls, *args, **kwargs):
        return ["GPIO-values",]

    def has_permission(self, user, action, pk):
        return True
    
def path_file_name(instance, filename):
    import os
    from django.core.files.storage import FileSystemStorage as fs
    from django.conf import settings
    filename, file_extension = os.path.splitext(filename)
    path='/'.join(filter(None, (instance.Code, 'thumbnail'+file_extension)))
    return path
    
class DeviceTypes(models.Model):
    
    Code = models.CharField(help_text=str(_('Unique identifier of the device type. Usually between 5 and 8 characters.')),unique=True, max_length=20)
    Description = models.CharField(max_length=100)
    MinSampletime=models.PositiveSmallIntegerField(help_text=str(_('Minimum accepted time between two polls. Refer to the device type documentation.')),default=10)
    Connection= models.PositiveSmallIntegerField(help_text=str(_('''The connection can be: 
                                                                    - LOCAL for devices that connect to a pin of the Master unit.
                                                                    - REMOTE OVER TCP for devices communicating through the WiFi interface.
                                                                    - MEMORY for devices that reside in the memory of the Master unit.''')),choices=CONNECTION_CHOICES)
    Picture = models.ImageField('DeviceType picture',
                                upload_to=path_file_name,
                                null=True,
                                blank=True)
                                
    def __str__(self):
        return self.Code
    
    def store2DB(self):
        self.full_clean()
        super().save() 
        
    class Meta:
        permissions = (
                        ("view_devicetypes", "Can see available device types"),
                    )
        verbose_name = _('Device type')
        verbose_name_plural = _('Device types')

@receiver(pre_delete, sender=DeviceTypes, dispatch_uid="delete_DeviceType")
def delete_DeviceType(sender, instance,**kwargs):
    instance.Picture.delete(False)
        
def initialize_polling_devices():
    from .tools import PollingScheduler
    scheduler=PollingScheduler(jobstoreUrl=POLLING_SCHEDULER_URL)
    scheduler.run()
    DVs=Devices.objects.all()
    if DVs.count()>0:
        for DV in DVs:
            DV.update_requests()
            
def request_callback(DV,DG,jobID,**kwargs): 
    if (DV.DVT.Connection==LOCAL_CONNECTION or DV.DVT.Connection==MEMORY_CONNECTION):
        import DevicesAPP.callbacks
        class_=getattr(DevicesAPP.callbacks, DV.DVT.Code)
        instance=class_(DV)
        status=instance(**kwargs)
    elif DV.DVT.Connection==REMOTE_TCP_CONNECTION:
        status=DV.request_datagram(DatagramId=DG.Identifier) 
    NextUpdate=DV.getNextUpdate(jobID=jobID) 
    DV.updatePollingStatus(LastUpdated=status['LastUpdated'],Error=status['Error'],NextUpdate=NextUpdate)

class Devices(models.Model):
                                    
    SQLcreateRegisterTable = ''' 
                                CREATE TABLE IF NOT EXISTS ? (
                                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    *
                                    UNIQUE (timestamp)                    
                                ); '''  # the * will be replaced by the column names and types
    SQLinsertRegister = ''' INSERT INTO %s(*) VALUES($) '''   # the * will be replaced by the column names and the $ by the values  
    
    class Meta:
        permissions = (
            ("view_devices", "Can see available devices"),
            ("scan_devices", "Can scan for new devices"),
            ("change_state_devices", "Can change the state of the devices"),
        )
        verbose_name = _('Slave Device')
        verbose_name_plural = _('Slave Devices')
        
    Name = models.CharField(help_text=str(_('Unique identifier of the device. Limited to 50 characters.')),
                            max_length=50,unique=True,error_messages={'unique':_("Invalid device name - This name already exists in the DB.")})
    IO = models.OneToOneField(MasterGPIOs,help_text=str(_('The pin of the Master unit to which the device is connected. Only applies to locally connected devices.')),
                            on_delete=models.CASCADE,related_name='pin2device',unique=True,null=True,blank=True)
    Code = models.PositiveSmallIntegerField(help_text=str(_('Unique byte-type identifier of the device. It is used to identify the device within the communication frames.')),
                            unique=True,blank=True,null=True,error_messages={'unique':_("Invalid device code - This code already exists in the DB.")})
    IP = models.GenericIPAddressField(protocol='IPv4', unique=True,blank=True,null=True,error_messages={'unique':_("Invalid IP - This IP already exists in the DB.")})
    DVT = models.ForeignKey(DeviceTypes,related_name="deviceType",on_delete=models.CASCADE)#limit_choices_to={'Connection': 'LOCAL'}
    State= models.PositiveSmallIntegerField(help_text=str(_('Polling state of the device. STOPPED = no polling.')),
                                            choices=STATE_CHOICES, default=0)
    Sampletime=models.PositiveSmallIntegerField(help_text=str(_('Elapsed time between two polls to the device.')),default=600)
    RTsampletime=models.PositiveSmallIntegerField(help_text=str(_('Elapsed time between two polls to the device on realtime polling.')),default=60)
    LastUpdated= models.DateTimeField(blank = True,null=True)
    NextUpdate= models.DateTimeField(blank = True,null=True)
    Connected = models.BooleanField(default=False)  # defines if the device is properly detected and transmits OK
    CustomLabels = models.CharField(max_length=1500,default='',blank=True) # json string containing the user-defined labels for each of the items in the datagrams
    Error= models.CharField(max_length=100,default='',blank=True)
    
    def _deviceType2Binding(self):
        '''THIS IS TO SEND ON THE DTATABINDING SOCKET THE CODE OF THE DEVICE TYPE. ON DEFAULT, IT SENDS THE pk '''
        return self.DVT.Code
    devicetype2str=property(_deviceType2Binding)
    
    def clean(self):
        if self.IO!=None:
            if self.IO.Direction!=GPIO_SENSOR:
                raise ValidationError(_('The GPIO selected is not configured as sensor'))
        if self.Sampletime<self.DVT.MinSampletime or self.RTsampletime<self.DVT.MinSampletime:
            raise ValidationError(_('The sample time selected is too low for the '+self.DVT.Code+' sensors. It should be greater than '+str(self.DVT.MinSampletime)+' sec.'))
        
    def __str__(self):
        return self.Name
    
    def __init__(self, *args, **kwargs):
        super(Devices, self).__init__(*args, **kwargs)
        
    def save(self, *args, **kwargs):
        super(Devices, self).save(*args, **kwargs)
    
    @staticmethod
    def getScheduler():
        from .tools import PollingScheduler
        scheduler=PollingScheduler(jobstoreUrl=POLLING_SCHEDULER_URL)
        return scheduler
        
    def stopPolling(self):
        if self.State==RUNNING_STATE:
            self.State=STOPPED_STATE
            self.save()
        self.update_requests()
    
    def startPolling(self):
        if self.State==STOPPED_STATE:
            self.State=RUNNING_STATE
            self.save()
        self.update_requests()
    
    def togglePolling(self):
        if self.State==STOPPED_STATE:
            self.startPolling()
        else:
            self.stopPolling()
            
    def getPollingJobIDs(self):
        DGs=Datagrams.objects.filter(DVT=self.DVT)
        jobIDs=[]
        if DGs != []:
            for DG in DGs:
                if DG.isSynchronous():
                    jobIDs.append({'id':self.Name + '-' + DG.Identifier,'DG':DG})
        return jobIDs
    
    def update_requests(self):
        
        scheduler=Devices.getScheduler()
        jobIDs=self.getPollingJobIDs()
        process=os.getpid()
        #logger.info("Enters update_requests on process " + str(process))
        
        if self.State==RUNNING_STATE:
            if jobIDs != []:
                numJobs=len(jobIDs)
                offset=self.Sampletime/numJobs
                now=datetime.datetime.now()
                for i,job in enumerate(jobIDs):
                    id=job['id']
                    DG=job['DG']
                    start_date=now+datetime.timedelta(seconds=i*offset+self.Sampletime/2)
                    JOB=scheduler.getJobInStore(jobId=id)
                    if JOB==None:     
                        callback="DevicesAPP.models:request_callback"
                        if self.DVT.Connection==LOCAL_CONNECTION: 
                            kwargs={'datagramId':DG.Identifier}
                            scheduler.add_job(func=callback,trigger='interval',id=id,args=(self,DG,id),kwargs=kwargs,seconds=self.Sampletime,start_date=start_date,
                                              replace_existing=True,max_instances=1,coalesce=True,misfire_grace_time=30)
                        elif self.DVT.Connection==REMOTE_TCP_CONNECTION:   
                            scheduler.add_job(func=callback,trigger='interval',id=id,args=(self, DG, id),seconds=self.Sampletime,start_date=start_date,
                                              replace_existing=True,max_instances=1,coalesce=True,misfire_grace_time=30)
                        elif self.DVT.Connection==MEMORY_CONNECTION:
                            kwargs={'datagramId':DG.Identifier}
                            scheduler.add_job(func=callback,trigger='interval',id=id,args=(self,DG,id), kwargs=kwargs,seconds=self.Sampletime,start_date=start_date,
                                              replace_existing=True,max_instances=1,coalesce=True,misfire_grace_time=30)
                        JOB=scheduler.getJobInStore(jobId=id)
                        if JOB!=None: 
                            text=str(_('Polling for the device '))+self.Name+str(_(' is started with sampletime= ')) + str(self.Sampletime) + str(_(' [s]. Next request at ') + str(JOB.next_run_time))
                            PublishEvent(Severity=0,Text=text,Persistent=True)
                        else:
                            PublishEvent(Severity=4,Text='Error adding job '+id+ ' to scheduler. Polling for device ' +self.Name+' could not be started' ,Persistent=True)
                            self.State=STOPPED_STATE
                            self.save()
                    else:
                        PublishEvent(Severity=0,Text='Requests '+id+ ' already was in the scheduler. ' + str(_('Next request at ') + str(JOB.next_run_time)),Persistent=True)
            else:        
                self.State=STOPPED_STATE
                self.save()
                text=str(_('Polling for device '))+self.Name+str(_(' could not be started. It has no Datagrams defined '))
                PublishEvent(Severity=3,Text=text,Persistent=True)
        else:
            if jobIDs != []:
                for job in jobIDs:
                    id=job['id']
                    JOB=scheduler.getJobInStore(jobId=id)
                    if JOB!=None: 
                        scheduler.remove_job(id)
                        JOBs=scheduler.getJobsInStore()
                        if JOB in JOBs:
                            self.State=RUNNING_STATE
                            self.save()
                            text='Polling for the device '+self.Name+' could not be stopped '
                            severity=5
                        else:
                            text='Polling for the device '+self.Name+' is stopped ' 
                            severity=0
                    else:
                        text=str(_('Job ')) + str(id) + str(_(' did not exist. The device ') + self.Name + str(_(' was already stopped.'))) 
                        severity=5  
            else:
                text='Unhandled error on update_requests for device ' + str(self.Name) 
                severity=5  
                
            PublishEvent(Severity=severity,Text=text,Persistent=True)
    
    def updatePollingStatus(self,LastUpdated,Error,NextUpdate):
        updateFields=['Error']
        if NextUpdate != None:
            self.NextUpdate=NextUpdate
            updateFields.append('NextUpdate')
        if LastUpdated!= None:
            self.LastUpdated=LastUpdated
            updateFields.append('LastUpdated')
            PublishEvent(Severity=0,Text=self.Name+str(_(' updated OK')),Persistent=True)
        self.Error=Error
        if Error!='':
            PublishEvent(Severity=3,Text=self.Name+' '+Error,Persistent=True)
            
        self.save(update_fields=updateFields)
        
        if 'LastUpdated' in updateFields:
            self.updateAutomationVars()
        
    def setLastUpdated(self,newValue):
        self.LastUpdated=newValue
        self.save(update_fields=['LastUpdated','Error','NextUpdate'])
    
    @staticmethod
    def getNextUpdate(jobID):
        if jobID!=None:
            scheduler=Devices.getScheduler()
            JOB=scheduler.getJobInStore(jobId=jobID)
            if JOB!=None:
                return JOB.next_run_time
        return None
            
    def setNextUpdate(self,jobID):
        next_run_time=Devices.getNextUpdate(jobID=jobID)
        self.NextUpdate=next_run_time
        if next_run_time==None:
            PublishEvent(Severity=3,Text='Next run time for job '+jobID+ ' could not be fetched.',Persistent=True)
        self.save(update_fields=['NextUpdate',])
        return next_run_time
        
    def setCustomLabels(self):
        DGs=Datagrams.objects.filter(DVT=self.DVT)
        if DGs.count()>0:
            if self.CustomLabels!='':
                CustomLabels=json.loads(self.CustomLabels)
            else:
                CustomLabels={}
            for DG in DGs:
                try:
                    kk=CustomLabels[str(DG.pk)]
                except:
                    CustomLabels[str(DG.pk)]={}
                datagram=DG.getStructure()
                names=datagram['names']
                for name in names:
                    if not name in CustomLabels[str(DG.pk)]:
                        info=Datagrams.getInfoFromItemName(name=name)
                        CustomLabels[str(DG.pk)][name]=info['human']
            self.CustomLabels=json.dumps(CustomLabels)
        else:
            self.CustomLabels=''
        self.save(update_fields=['CustomLabels',])
    
    def getRegistersTables(self,DG=None):
        if DG==None:
            DGs=Datagrams.objects.filter(DVT=self.DVT)
            tables=[]
            if DGs.count()>0:
                for DG in DGs:
                    tables.append(self.getRegistersDBTableName(DG=DG))
        else:
            tables=self.getRegistersDBTableName(DG=DG)
        return tables
    
    def getLatestData(self):
        DGs=Datagrams.objects.filter(DVT=self.DVT)
        if self.CustomLabels=='':
            self.setCustomLabels()
            
        Data={}
        if DGs.count()>0:
            CustomLabels=json.loads(self.CustomLabels)
            for DG in DGs:
                Data[str(DG.pk)]={}
                table=self.getRegistersTables(DG=DG)
                vars='"timestamp"'
                for name in CustomLabels[str(DG.pk)]:
                    vars+=',"'+name+'"'
                sql='SELECT '+vars+' FROM "'+ table +'" ORDER BY timestamp DESC LIMIT 1'
                from utils.BBDD import getRegistersDBInstance
                DB=getRegistersDBInstance()
                row=DB.executeTransaction(SQLstatement=sql)
                if row != []:
                    row=row[0]
                    timestamp=row[0]
                    row=row[1:]
                else:
                    timestamp=None
                    row=None
                if CustomLabels!=None:
                    Data[str(DG.pk)]['timestamp']=timestamp
                    for i,name in enumerate(CustomLabels[str(DG.pk)]):
                        info=Datagrams.getInfoFromItemName(name=name)
                        if row==None:
                            Data[str(DG.pk)][name]=row
                        else:
                            if info['type']!=DTYPE_DIGITAL:
                                Data[str(DG.pk)][name]=row[i]
                            else:
                                from utils.dataMangling import checkBit
                                values={}
                                for k in range(0,8):
                                    values['bit' + str(k)]=int(checkBit(number=row[i],position=k))
                                Data[str(DG.pk)][name]=values
        else:
            Data=None
        return Data
        
    def getDeviceVariables(self):
        DeviceVars=[]
        DGs=Datagrams.objects.filter(DVT=self.DVT)
        if self.CustomLabels!='':
            CustomLabels=json.loads(self.CustomLabels)
        else:
            CustomLabels=None
            
        for DG in DGs:
            datagram=DG.getStructure()
            names=datagram['names']
            types=datagram['types']
            table=self.getRegistersTables(DG=DG)
            if CustomLabels!=None:
                CustomVars=CustomLabels[str(DG.pk)]
            else:
                CustomVars={}
                for name,type in zip(names,types):
                    if type==DTYPE_DIGITAL:
                        CustomVars[name]=''
                        for i in range(0,8):
                            CustomVars[name]+='$'+name+' bit ' + str(i)
                        CustomVars[name]=CustomVars[name][1:]
                    else:
                        CustomVars[name]=name
                
            for name,type in zip(names,types):
                if type==DTYPE_DIGITAL:
                    BitLabels=CustomVars[name].split('$')
                    if len(BitLabels)==8:
                        for i,bitLabel in enumerate(BitLabels):
                            DeviceVars.append({'label':bitLabel,'name':name,'device':self.pk,'table':table,'bit':i,'sample':datagram['sample']*self.Sampletime})
                    else:
                        raise DevicesAppException(str(_('The variable named '))+ name + str(_(' is registered as digital but does not have 8 bit labels chained by character "$" ')))
                else:
                    DeviceVars.append({'label':CustomVars[name],'name':name,'device':self.pk,'table':table,'bit':None,'sample':datagram['sample']*self.Sampletime})
        return DeviceVars
    
    def updateAutomationVars(self):
        AutomationVars=HomeAutomation.models.AutomationVariablesModel.objects.filter(Device=self.pk)
        DeviceVars=self.getDeviceVariables()
        for dvar in DeviceVars:
            try:
                avar=AutomationVars.get(Tag=dvar['name'],Table=dvar['table'],Device=dvar['device'],BitPos=dvar['bit'])
            except:
                avar=None
                
            if avar==None:
                avar=HomeAutomation.models.AutomationVariablesModel()
                avar.create(Label=dvar['label'],Tag=dvar['name'],Device=dvar['device'],Table=dvar['table'],BitPos=dvar['bit'],Sample=dvar['sample'])
            
            avar.executeAutomationRules()
            
    def deleteAutomationVars(self):
        HomeAutomation.models.AutomationVariablesModel.objects.filter(Device=self.pk).delete()
            
    @staticmethod
    def parseDeviceConfFile(xmlroot):
        """
        EXTRACTS THE INFORMATION FROM THE CONFIGURATION FILE SENT BY THE DEVICE
        """
        
        node=xmlroot.find('DEVT')
        if node==None:
            raise DevicesAppException('The device responded with an improper Conf.xml file, deviceType tag <DEVT> could not be found: ' + str(xmlroot.text))
        TYPE=node.text
        node=xmlroot.find('DEVC')
        if node==None:
            raise DevicesAppException('The device responded with an improper Conf.xml file, deviceCode tag <DEVC> could not be found: ' + str(xmlroot.text))
        CODE=node.text
        # node=xmlroot.find('DEVIP')
        # if node==None:
            # raise DevicesAppException('The device responded with an improper Conf.xml file, deviceIP tag <DEVIP> could not be found: ' + str(xmlroot.text))
        # DEVICE_IP=node.text.replace(',','.')
        IP=""
        return (TYPE,CODE,IP)   
    
    @staticmethod
    def parseDatagram(xmlroot):
        """
        :callback            datagram=myHttp.buildDatagram(xmlroot)
        :return datagram with structure (DeviceCode,DatagramId,data0,data1...dataN)
        """
        from utils.dataMangling import Bytes2Float32
        datagram=[]
        result=2
        for child in xmlroot:
            if child.tag=='VAR':
                integerValue=int(child.text)
                datagram.append(integerValue)
                #for i in range(0,8):
                    #print('Position ' + str(i) + ':',self.checkBit(integerValue, i))
            elif child.tag=='AV':
                floatValueBytes=[int(i) for i in child.text.split(',')]
                floatValueBin=(floatValueBytes[0]<<24)|(floatValueBytes[1]<<16)|(floatValueBytes[2]<<8)|(floatValueBytes[3])
                floatValue=Bytes2Float32(floatValueBin)
                datagram.append(floatValue)
            elif child.tag=='DEV':  # 
                datagram.insert(0,child.text)
                result-=1
            elif child.tag=='DId':
                datagram.insert(1,child.text)
                result-=1            
        return (result,datagram)
    
    @classmethod
    def scan(cls,FormModel,IP=None):
        if IP==None:
            IP=DEVICES_SUBNET+DEVICES_SCAN_IP4BYTE
        server=DEVICES_PROTOCOL + IP
        #server='http://127.0.0.1'
        (status,root)=cls.request_confXML(server=server,xmlfile=DEVICES_CONFIG_FILE)
        errors=[]
        
        if status==200:
            (DEVICE_TYPE,DEVICE_CODE,DEVICE_IP) =cls.parseDeviceConfFile(xmlroot=root)
            try:
                Type=DeviceTypes.objects.get(Code=DEVICE_TYPE)
            except DeviceTypes.DoesNotExist: 
                Type=None
                errors.append(_('Unknown Device type: ') + DEVICE_TYPE + str(_('. You should firstly register the Device type.')))
                
            lastRow=Devices.objects.all().count()                     
            DeviceName='Device'+str(lastRow+1)
            DeviceType=DEVICE_TYPE
            DEVICE_CODE=lastRow+1+IP_OFFSET
            DeviceIP=DEVICES_SUBNET+str(DEVICE_CODE)
            payload={'DEVC':str(DEVICE_CODE)}
            (status,r)=cls.request_orders(server=server,order='SetConf.htm',payload=payload)
            if status==200 and Type!=None:
                form=FormModel(action='add',initial={'Name':DeviceName,'DVT':Type,'Code':DEVICE_CODE,'IP':DeviceIP})
                state='ConfigOK'
            else:
                DEVICE_CODE=0
                DeviceIP=IP
                form=FormModel(action='scan',initial={'Name':DeviceName,'DVT':Type,'Code':DEVICE_CODE,'IP':DeviceIP})
                state='ConfigNoOK'
                if Type!=None:
                    errors.append(_('Device did not acknowledge the "SetConf" order. Revise the Device source code.'))
        else:
            state='Nothing'
            DEVICE_TYPE=None
            form=FormModel(action='scan',initial={'Name':'','Type':'','Code':'','IP':''})
        return {'devicetype':DEVICE_TYPE,'Form':form,'errors':errors}
    
    @staticmethod
    def request_orders(server,order,payload,timeout=1):
        """
        :callback       payload = {'key1': 'value1', 'key2': 'value2'}   
                        self.orders_request(server, 'orders', payload) 
        """
        import requests
        import random
        try:
            r = requests.post(server+'/orders/'+order,params=payload,timeout=timeout)
            if r.status_code==200:
                return (200,r)
            else:
                return (r.status_code,None)
        except:
            logger.error("Unexpected error in orders_request:"+ str(sys.exc_info()[1])) 
            return (100,None)
        
    @staticmethod
    def request_confXML(server,xmlfile,timeout=1):
        """
        Requests a xml file from a server
        :param server: 
        :param xmlfile:
        :return: root to the xml. Server error code if error
        :callback:      xmlfile='angles.xml'
                        xmlroot=myHttp.xml_request(server, xmlfile)
        """
        import requests
        import random
        try:
            import xml.etree.ElementTree as ET
            r = requests.get(server+'/'+xmlfile+'?t='+str(random.random()),timeout=timeout)     
            if r.status_code==200:
                root = ET.fromstring(r.text)                
                return (r.status_code,root)
            else:
                return (r.status_code,None)
        except:
            logger.error("Unexpected error in xml_data_request:"+ str(sys.exc_info()[1])) 
            return (100,None)
        
    def getRegistersDBTableName(self,DG):
        return str(self.pk)+'_'+str(DG.pk)
    
    def _createRegistersTable(self,DG,Database):
        """
        Creates the table corresponding to the DV and Datagram DG
        """
        TableName=self.getRegistersDBTableName(DG=DG)
        datagram=DG.getStructure()
        names=datagram['names']
        datatypes=datagram['datatypes']        
        logger.info('Creating "'+TableName+'" table with:')
        logger.info('   - DeviceType='+str(self.DVT))
        logger.info('   - fieldNames'+str(names)) 
        logger.info('   - fieldTypes'+str(datatypes))  
        fieldNames=names
        fieldTypes=datatypes
        try:
            if len(fieldNames)!=len(fieldTypes):
                logger.error('The length of the lists of names and types does not match in create_datagram_table')
                raise ValueError('The length of the lists of names and types does not match')
            else:
                temp_string=''
                for i in range(0,len(fieldNames)):
                    temp_string+='"'+fieldNames[i] + '" ' + fieldTypes[i] + ','
                sql=self.SQLcreateRegisterTable.replace('*',temp_string).replace('?','"'+TableName+'"')
                result=Database.executeTransactionWithCommit(SQLstatement=sql, arg=[])
                if result==0:
                    logger.info('Succeded in creating the table "'+TableName+'"') 
        except:
            text = str(_("Error in create_datagram_table: ")) + str(sys.exc_info()[1]) 
            raise DevicesAppException(text)
            PublishEvent(Severity=5,Text=text + 'SQL: ' + sql,Persistent=True)
            #logger.error ("Unexpected error in create_datagram_table:"+ str(sys.exc_info()[1]))
    
    def createRegistersTables(self,Database):
        """
        CREATES ALL REGISTERS TABLE:
        """
        DGs=Datagrams.objects.filter(DVT=self.DVT)
        for DG in DGs:
            self._createRegistersTable(DG=DG,Database=Database)
            
    def getInsertRegisterSQL(self,DatagramId):
        DG = Datagrams.objects.get(DVT=self.DVT,Identifier=DatagramId)
        datagram=DG.getStructure()
        
        names=datagram['names']
        types=datagram['datatypes']
        sql=self.SQLinsertRegister
        #SQLinsertRegister = ''' INSERT INTO %s(*) VALUES($) '''   # the * will be replaced by the column names and the $ by the values  
        temp_string1='?,'
        temp_string2='timestamp,' 
        for i in range(0,len(names)):
            if (names[i].find('$')>=0): # names[i]=STATUS_bits_Alarm0;Alarm1;Alarm2;Alarm3;Alarm4;Alarm5;Alarm6;Alarm7 
                                        #to remove the char ; from the name of the columns
                tempname=names[i].split('_')
                name=tempname[0]
                for component in tempname[1:]:
                    if '$' in component: # found the $ item meaning bit labels
                        break
                    name=name+'_'+component
                name=name
            else:
                name=names[i]
                
            if i<len(names)-1:
                temp_string1+= '?,'
                temp_string2+='"'+name+'"'+ ','
            else:
                temp_string1+='?'
                temp_string2+='"'+name+'"'
                
        sql=sql.replace('*',temp_string2)        
        sql=sql.replace('$',temp_string1).replace('%s','"'+str(self.pk)+'_'+str(datagram['pk'])+'"')
        return {'query':sql,'num_args':len(names)}
    
    
    def checkRegistersDB(self,Database):
        
        rows=Database.retrieve_DB_structure(fields='*')   #('table', 'devices', 'devices', 4, "CREATE TABLE devices...)
        
        required_DGs=[]
            
        DGs=Datagrams.objects.filter(DVT=self.DVT)
        for DG in DGs:
            found=False
            table_to_find=self.getRegistersDBTableName(DG=DG)
            for row in rows:
                if (row[1]==table_to_find):   # found the table in the DB
                    found=True
                    datagram=DG.getStructure()
                    Database.checkTableColumns(table=table_to_find,desiredColumns={'names':datagram['names'],'datatypes':datagram['datatypes']})
                    break
            if found is not True:
                required_DGs.append(DG) 
                logger.info('The table '+table_to_find+' was not created.')
            
        for DG in required_DGs:
            self._createRegistersTable(DG=DG,Database=Database)
            
    def insertRegister(self,TimeStamp,DatagramId,year,values,NULL=False):
        """
        INSERTS A REGISTER IN THE registersDB INTO THE APPROPIATE TABLE.
        """
        try:                              
            TimeStamp=TimeStamp.replace(microsecond=0)
            
            query=self.getInsertRegisterSQL(DatagramId=DatagramId)
            sql=query['query']
            num_args=query['num_args']
            roundvalues=[TimeStamp,]
            if NULL==False:
                for i in range(0,num_args): 
                    try:
                        roundvalues.append(round(values[i],3))
                    except:
                        roundvalues.append(values[i])
            else:
                logger.info('Inserted NULL values on device ' + self.Name)  
                for i in range(0,num_args):  
                    roundvalues.append(None)
                    
            from utils.BBDD import getRegistersDBInstance
            DB=getRegistersDBInstance(year=TimeStamp.year)
            self.checkRegistersDB(Database=DB)
            DB.executeTransactionWithCommit(SQLstatement=sql, arg=roundvalues)
        except:
            raise DevicesAppException("Unexpected error in insert_device_register:" + str(sys.exc_info()[1]))
            
    def request_datagram(self,DatagramId,timeout=1,writeToDB=True,resetOrder=True,retries=1):
        """
        Requests a xml file from a server
        :param Name
        :param Code:
        :param DatagramId: DatagramId='angles.xml'
        
        :callback:      

        """
        import xml.etree.ElementTree as ET
        import requests
        import random
        import time
            
        server=DEVICES_PROTOCOL+str(self.IP)
        
        timestamp=timezone.now().replace(microsecond=0) #para hora con info UTC
        
        LastUpdated=None
        out={'values':None,'Error':None,'LastUpdated':None}
        while retries>=0 and out['values']==None:
            try:
                r = requests.get(server+'/'+DatagramId+'.xml?t='+str(random.random()),timeout=timeout)
                if r.status_code==200:
                    root = ET.fromstring(r.text)
                    result,datagram=self.parseDatagram(xmlroot=root)
                    if result==0:
                        deviceCode=datagram[0]
                        if int(deviceCode)==self.Code:
                            del datagram[0:2]
                            Error=''
                            if writeToDB:
                                self.insertRegister(TimeStamp=timestamp, DatagramId=DatagramId, 
                                                                  year=timestamp.year, values=datagram,NULL=False)
                                if resetOrder:
                                    (code,x) = self.request_orders(server=server,order='resetStatics',payload={})
                                    if code==200:
                                        Error=''
                                    else:
                                        Error='The device did not acknowledge the resetStatics order on datagram ' + DatagramId
                            out['values']=[round(x,3) for x in datagram]
                            out['LastUpdated']=timestamp
                            
                        else:
                            Error='The device responded with a different DeviceCode than the one expected on datagram ' + DatagramId
                            out['values']=None
                            out['LastUpdated']=None
                    else:
                        Error='Error in the format of the datagram received'
                        out['values']=None
                        out['LastUpdated']=None
                else:
                    Error='Error HTTP ' + str(r.status_code)
                    out['values']=None
                    out['LastUpdated']=None
                out['Error']=Error
            except:
                if str(sys.exc_info()[0]).find('ConnectTimeout')>=0:
                    if retries>0:
                        Error=self.Name+" did not respond within the timeout margin (default 1 sec)"
                    else:
                        Error="Finished retrying request to " + self.Name
                else:
                    raise DevicesAppException('Unknown error: ' + str(sys.exc_info()[1]))
                
                if retries==0 and writeToDB:
                    self.insertRegister(TimeStamp=timestamp, DatagramId=DatagramId, 
                                        year=timestamp.year, values=[],NULL=True)
                    
                out['Error']=Error
                out['values']=None
                out['LastUpdated']=None
            retries-=1
            if out['values']==None:
                time.sleep(1)
        return out
    
    def deleteRegistersTables(self):
        from utils.BBDD import getRegistersDBInstance
        DGs=Datagrams.objects.filter(DVT=self.DVT)
        DB=getRegistersDBInstance()
        for DG in DGs:
            table=self.getRegistersDBTableName(DG=DG)
            DB.dropTable(table=table)

        
@receiver(post_save, sender=Devices, dispatch_uid="update_Devices")
def update_Devices(sender, instance, update_fields,**kwargs):
    if kwargs['created']:   # new instance is created
        from utils.BBDD import getRegistersDBInstance
        DB=getRegistersDBInstance(year=None)
        instance.createRegistersTables(Database=DB)
        instance.update_requests()
               
@receiver(post_delete, sender=Devices, dispatch_uid="delete_Devices")
def delete_Devices(sender, instance,**kwargs):
    instance.deleteAutomationVars()
    logger.info('Se ha eliminado el dispositivo ' + str(instance))

class DevicesBinding(WebsocketBindingWithMembers):

    model = Devices
    stream = "Device_params"
    fields = ["Name","IO","Code","IP","Type","Sampletime","State","LastUpdated","Error","devicetype2str"]

    @classmethod
    def group_names(cls, *args, **kwargs):
        return ["Device-models",]

    def has_permission(self, user, action, pk):
        return True
        
        
class DatagramItems(models.Model):
    
    class Meta:
        verbose_name = _('Datagram item')
        verbose_name_plural = _('Datagram items')
        
    Tag = models.CharField(max_length=20,unique=True)
    DataType= models.CharField(max_length=20,choices=DATATYPE_CHOICES)
    PlotType= models.PositiveSmallIntegerField(choices=PLOTTYPE_CHOICES,default=SPLINE_PLOT)
    Units = models.CharField(max_length=10,null=True,blank=True)
    
    def clean(self):
        if self.DataType==DTYPE_DIGITAL:
            self.Units='bits'
            self.PlotType=LINE_PLOT

    def store2DB(self):
        self.full_clean()
        super().save() 
        
    def __str__(self):
        return self.Tag
    
    def getHumanName(self):
        return self.Tag+'_'+self.Units
    
    
        
class Datagrams(models.Model):
    
    class Meta:
        verbose_name = _('Datagram')
        verbose_name_plural = _('Datagrams')
        unique_together = (('DVT', 'Identifier'),('DVT', 'Code'))
        
    Identifier = models.CharField(max_length=20)
    Code= models.PositiveSmallIntegerField(help_text='Identifier byte-type code')
    Type= models.PositiveSmallIntegerField(choices=DATAGRAMTYPE_CHOICES)
    DVT = models.ForeignKey(DeviceTypes,on_delete=models.CASCADE)
    ITMs = models.ManyToManyField(DatagramItems, through='ItemOrdering')
    
    def __str__(self):
        return self.Identifier
    
    def clean(self):
        pass
        
    def store2DB(self):
        self.full_clean()
        super().save() 
        
    def isSynchronous(self):
        return int(self.Type==DG_SYNCHRONOUS)
    
    def getDBTypes(self):
        types=[]
        for item in self.itemordering_set.all():
            if item.ITM.DataType!= DTYPE_DIGITAL:
                types.insert(item.Order-1,'analog')
            else:
                types.insert(item.Order-1,'digital')
        types.insert(0,'datetime')
        return types
    
    @staticmethod
    def getInfoFromItemName(name):
        info=name.split('_')
        if len(info)==3:
            try:
                IT=DatagramItems.objects.get(pk=int(info[0]))
                return {'itempk':info[0],'numitem':info[1],'datagrampk':info[2],'type':IT.DataType,'units':IT.Units,'human':IT.getHumanName()}
            except:
                raise DevicesAppException(str(_('The datagram item name ')) + str(name) + str(_(' raised exception when getting its info.')))
        else:
            raise DevicesAppException(str(_('The datagram item name ')) + str(name) + str(_(' does not have the proper structure "Item.pk_NumItem_Datagram.pk"')))
            
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
        for ITO in self.itemordering_set.all().order_by('Order'):
            numItems=1
            if not str(ITO.ITM.pk) in checkedPK:
                checkedPK[str(ITO.ITM.pk)]=1
            else:
                numItems=checkedPK[str(ITO.ITM.pk)]+1
                checkedPK[str(ITO.ITM.pk)]+=1
            names.insert(ITO.Order-1,str(ITO.ITM.pk)+'_'+str(numItems)+'_'+str(self.pk))
            units.insert(ITO.Order-1,ITO.ITM.Units)
            plottypes.insert(ITO.Order-1,ITO.ITM.PlotType)
            if ITO.ITM.DataType!= DTYPE_DIGITAL:
                types.insert(ITO.Order-1,ITO.ITM.DataType)
                datatypes.insert(ITO.Order-1,ITO.ITM.DataType)
            else:
                types.insert(ITO.Order-1,ITO.ITM.DataType)
                datatypes.insert(ITO.Order-1,'INTEGER')
        if self.isSynchronous():
            sample=1
        else:
            sample=0
        
        return {'pk':self.pk,'ID':datagramID,'names':names,'types':types,'datatypes':datatypes,'units':units,'plottypes':plottypes,'sample':sample}


@receiver(post_save, sender=Datagrams, dispatch_uid="update_Datagrams")
def update_Datagrams(sender, instance, update_fields,**kwargs):
    if not kwargs['created']:   # an instance has been modified
        logger.info('Se ha modificado el datagram ' + str(instance.DeviceType)+"_"+str(instance))
        DVs=Devices.objects.filter(Type=instance.DeviceType)
        if DVs.count()>0:
            for DV in DVs:
                DV.updateAutomationVars()
                from utils.BBDD import getRegistersDBInstance
                DB=getRegistersDBInstance()
                DV.checkRegistersDB(Database=DB)
                DV.updateCustomLabels()
    else:
        logger.info('Se ha creado el datagram ' + str(instance.DVT)+"_"+str(instance))
        logger.info('Tiene ' + str(instance.ITMs.count())+' ' + (DatagramItems._meta.verbose_name.title() if (instance.ITMs.count()==1) else DatagramItems._meta.verbose_name_plural.title()))
        for item in instance.ITMs.all():
            logger.info('   - ' + str(item.Tag))

    
class ItemOrdering(models.Model):
    DG = models.ForeignKey(Datagrams, on_delete=models.CASCADE)
    ITM = models.ForeignKey(DatagramItems, on_delete=models.CASCADE,blank=True,null=True)
    Order = models.PositiveSmallIntegerField(help_text='Position in the dataframe 1-based')
    
    def __str__(self):
        return str(self.datagram) + ':' +str(self.order)
        
    class Meta:
        verbose_name = _('Item')
        verbose_name_plural = _('Items')
        ordering = ('Order',)
        

class DeviceCommands(models.Model):
    DVT = models.ForeignKey(DeviceTypes,on_delete=models.CASCADE)
    Identifier = models.CharField(max_length=10)
    HumanTag = models.CharField(max_length=50)
    
    def __str__(self):
        return self.HumanTag
        
    class Meta:
        verbose_name = _('Command')
        verbose_name_plural = _('Commands')
        unique_together = ('DVT', 'Identifier',)
        
class Beacons(models.Model):
    Identifier = models.CharField(max_length=20,unique=True,error_messages={'unique':_("Invalid Beacon name - This name already exists in the DB.")})
    Latitude = models.FloatField()
    Longitude = models.FloatField()
    WeatherObserver=models.OneToOneField(Devices,on_delete=models.CASCADE,related_name='device2beacon',
                                         null=True,blank=True,limit_choices_to={'Type__Code': 'OpenWeatherMap'})
    
    @staticmethod
    def distance_to(other):
        from math import sin, cos, sqrt, atan2, radians
        # approximate radius of earth in km
        R = 6373.0
        lat1 = radians(self.Latitude)
        lon1 = radians(self.Longitude)
        lat2 = radians(other.Latitude)
        lon2 = radians(other.Longitude)
        
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        distance = R * c
        return round(distance,1)
    
    def __str__(self):
        return self.Identifier
    
