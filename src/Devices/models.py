from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from django.dispatch import receiver
from django.db.models.signals import post_save,post_delete,pre_delete
from django.db.models.signals import m2m_changed

from channels.binding.websockets import WebsocketBinding

from Master_GPIOs.models import IOmodel
#import LocalDevices.models 
#import RemoteDevices.models 
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
    Description = models.CharField(max_length=50)
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



class DeviceModel(models.Model):
    
    STATE_CHOICES=(
        ('STOPPED','STOPPED'),
        ('RUNNING','RUNNING')
    )
    
    __original_DeviceName = None
    
    DeviceName = models.CharField(max_length=50,unique=True,error_messages={'unique':_("Invalid device name - This name already exists in the DB.")})
    IO = models.OneToOneField(IOmodel,on_delete=models.CASCADE,related_name='pin2device',unique=True,null=True,blank=True)
    DeviceCode = models.IntegerField(unique=True,blank=True,null=True,error_messages={'unique':_("Invalid device code - This code already exists in the DB.")})
    DeviceIP = models.GenericIPAddressField(protocol='IPv4', unique=True,blank=True,null=True,error_messages={'unique':_("Invalid IP - This IP already exists in the DB.")})
    Type = models.ForeignKey(DeviceTypeModel,related_name="deviceType",on_delete=models.CASCADE)#limit_choices_to={'Connection': 'LOCAL'}
    DeviceState= models.CharField(choices=STATE_CHOICES, max_length=15,default='STOPPED')
    Sampletime=models.PositiveIntegerField(default=600)
    RTsampletime=models.PositiveIntegerField(default=60)
    LastUpdated= models.DateTimeField(blank = True,null=True)
    Connected = models.BooleanField(default=False)  # defines if the device is properly detected and transmits OK
    CustomLabels = models.CharField(max_length=1500,default='',blank=True) # json string containing the user-defined labels for each of the items in the datagrams
    Error= models.CharField(max_length=100,default='',blank=True)
    
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
            #LocalDevices.signals.DeviceName_changed.send(sender=None, OldDeviceName=self.__original_DeviceName,NewDeviceName=self.DeviceName)
        self.__original_DeviceName = self.DeviceName
        super(DeviceModel, self).save(*args, **kwargs)
        
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
            if CustomLabels!=None:
                CustomVars=CustomLabels[DG.Identifier]
            else:
                CustomVars={}
                for name in datagram['names']:
                    CustomVars[name]=name
                
            for cvar,var,type in zip(CustomVars,Vars,Types):
                if type=='digital':
                    BitLabels=CustomVars[cvar].split('$')
                    for i,bitLabel in enumerate(BitLabels):
                        DeviceVars.append({'Label':bitLabel,'Tag':var,'Device':self.pk,'Table':str(self.pk)+'_'+str(datagram['pk']),'BitPos':i,'Sample':datagram['sample']*self.Sampletime})
                else:
                    DeviceVars.append({'Label':CustomVars[cvar],'Tag':var,'Device':self.pk,'Table':str(self.pk)+'_'+str(datagram['pk']),'BitPos':None,'Sample':datagram['sample']*self.Sampletime})
        return DeviceVars
    
    def updateAutomationVars(self):
        AutomationVars=HomeAutomation.models.AutomationVariablesModel.objects.filter(Device=self.pk)
        DeviceVars=self.getDeviceVariables()
        for dvar in DeviceVars:
            try:
                avar=AutomationVars.get(Tag=dvar['Tag'],Table=dvar['Table'],Device=dvar['Device'],BitPos=dvar['BitPos'])
            except:
                avar=None
                
            if avar!=None:
                avar.Label=dvar['Label']
                avar.Sample=dvar['Sample']
            else:
                avar=HomeAutomation.models.AutomationVariablesModel()
                avar.Label=dvar['Label']
                avar.Device=dvar['Device']
                avar.Tag=dvar['Tag']
                avar.Table=dvar['Table']
                avar.BitPos=dvar['BitPos']
                avar.Sample=dvar['Sample']
            avar.save()
            
    def deleteAutomationVars(self):
        HomeAutomation.models.AutomationVariablesModel.objects.filter(Device=self.DeviceName).delete()
            
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
    else:
        instance.updateAutomationVars()
        
@receiver(post_delete, sender=DeviceModel, dispatch_uid="delete_DeviceModel")
def delete_DeviceModel(sender, instance,**kwargs):
    instance.deleteAutomationVars()
    logger.info('Se ha eliminado el dispositivo ' + str(instance))

class DeviceModelBinding(WebsocketBinding):

    model = DeviceModel
    stream = "RDevice_params"
    fields = ["DeviceName","IO","DeviceCode","DeviceIP","Type","Sampletime","DeviceState","LastUpdated","Error"]

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
    
    def getReport(self):
        from Devices.Reports import get_report
        import datetime
        if self.Periodicity==2: # daily report
            offset=datetime.timedelta(hours=24)
        elif self.Periodicity==3: # weekly report
            offset=datetime.timedelta(weeks=1)
        elif self.Periodicity==4: # monthly report  BEWARE!!
            offset=datetime.timedelta(hours=30*24)
        toDate=timezone.now() 
        fromDate=toDate-offset
        toDate=toDate-datetime.timedelta(minutes=1)
        reportData=get_report(reporttitle=self.ReportTitle,fromDate=fromDate,toDate=toDate,aggregation=self.DataAggregation)
        return reportData,fromDate,toDate
        #reportData= {'reportTitle': 'Prueba1', 'fromDate': datetime.datetime(2017, 8, 30, 9, 14, 38), 'toDate': datetime.datetime(2017, 8, 31, 2, 0), 
        # 'charts': [{'chart_title': 'Temperatura', 'cols': [{'table': 'Ambiente en salon_data', 'name': 'Temperature_degC', 'label': 'Temperature_degC', 'type': 'number', 'bitPos': None}, {'table': 'Ambiente en salon_data', 'name': 'Heat Index_degC', 'label': 'Heat Index_degC', 'type': 'number', 'bitPos': None}], 'rows': {'x_axis': [{'v': 'Date(2017,7,30,9,30,0)'}, {'v': 'Date(2017,7,30,10,30,0)'}, {'v': 'Date(2017,7,30,11,30,0)'}, {'v': 'Date(2017,7,30,12,30,0)'}, {'v': 'Date(2017,7,30,13,30,0)'}, {'v': 'Date(2017,7,30,14,30,0)'}, {'v': 'Date(2017,7,30,15,30,0)'}, {'v': 'Date(2017,7,30,16,30,0)'}, {'v': 'Date(2017,7,30,17,30,0)'}, {'v': 'Date(2017,7,30,18,30,0)'}, {'v': 'Date(2017,7,30,19,30,0)'}, {'v': 'Date(2017,7,30,20,30,0)'}, {'v': 'Date(2017,7,30,21,30,0)'}, {'v': 'Date(2017,7,30,22,30,0)'}, {'v': 'Date(2017,7,30,23,30,0)'}, {'v': 'Date(2017,7,31,0,30,0)'}, {'v': 'Date(2017,7,31,1,30,0)'}], 'y_axis': [[26.6, 0.0], [26.916666666666664, 0.0], [27.0, 0.0], [27.02777777777778, 0.0], [27.12121212121212, 0.0], [27.44827586206896, 0.0], [28.0, 0.0], [28.0, 0.0], [28.0, 0.0], [28.0, 0.0], [28.0, 0.0], [27.583333333333332, 0.0], [27.138888888888893, 0.0], [27.055555555555557, 0.0], [27.138888888888893, 0.0], [27.0, 0.0], [27.0, 0.0]]}}, 
        #           {'chart_title': 'Humedad', 'cols': [{'table': 'Ambiente en salon_data', 'name': 'RH_pc', 'label': 'RH_pc', 'type': 'number', 'bitPos': None}], 'rows': {'x_axis': [{'v': 'Date(2017,7,30,9,30,0)'}, {'v': 'Date(2017,7,30,10,30,0)'}, {'v': 'Date(2017,7,30,11,30,0)'}, {'v': 'Date(2017,7,30,12,30,0)'}, {'v': 'Date(2017,7,30,13,30,0)'}, {'v': 'Date(2017,7,30,14,30,0)'}, {'v': 'Date(2017,7,30,15,30,0)'}, {'v': 'Date(2017,7,30,16,30,0)'}, {'v': 'Date(2017,7,30,17,30,0)'}, {'v': 'Date(2017,7,30,18,30,0)'}, {'v': 'Date(2017,7,30,19,30,0)'}, {'v': 'Date(2017,7,30,20,30,0)'}, {'v': 'Date(2017,7,30,21,30,0)'}, {'v': 'Date(2017,7,30,22,30,0)'}, {'v': 'Date(2017,7,30,23,30,0)'}, {'v': 'Date(2017,7,31,0,30,0)'}, {'v': 'Date(2017,7,31,1,30,0)'}], 'y_axis': [[29.4], [29.083333333333336], [29.0], [29.027777777777782], [29.0], [29.0], [29.0], [29.0], [29.0], [29.0], [29.0], [29.0], [29.0], [29.0], [29.027777777777782], [29.0], [29.0]]}}]}

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
    HumanTag = models.CharField(max_length=20,unique=True)
    DataType= models.CharField(max_length=10,choices=DATATYPE_CHOICES)
    Units = models.CharField(max_length=10,null=True,blank=True)
    
    def clean(self):
        if self.DataType=='DIGITAL':
            self.Units='bits'
                        
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
        
        return {'pk':self.pk,'ID':datagramID,'names':names,'types':types,'datatypes':datatypes,'units':units,'sample':sample}

    class Meta:
        verbose_name = _('Datagram')
        verbose_name_plural = _('Datagrams')
        unique_together = (('DeviceType', 'Identifier'),('DeviceType', 'Code'))
       
@receiver(post_save, sender=DatagramModel, dispatch_uid="update_DatagramModel")
def update_DatagramModel(sender, instance, update_fields,**kwargs):
    if not kwargs['created']:   # an instance has been modified
        logger.info('Se ha modificado el datagram ' + str(instance.DeviceType)+"_"+str(instance))
        
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
                                'label':[IO.label,],'extrapolate':'keepPrevious','type':'digital'})# this is to tell the template that it is a boolean value
                                
        info.append({'deviceName':'Main','variables':tempvars})
    tempvars=[]
    if len(MainVars)>0:
        for VAR in MainVars:
            table='MainVariables'
            tempvars.append({'device':'Main','table':table,'tag':str(VAR.pk),
                            'label':VAR.Label,'extrapolate':'keepPrevious','type':'analog'})
                                
        info.append({'deviceName':'Main','variables':tempvars})
        
    for DV in DVs:    # device[0]= DeviceName, device[1]=DeviceType  
        DGs=Devices.models.DatagramModel.objects.filter(DeviceType=DV.Type)#XMLParser.getDatagramsStructureForDeviceType(deviceType=DEVICE_TYPE)
        tempvars=[]
        for DG in DGs: 
            table=str(DV.pk)+'_'+str(DG.pk)
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
                    tempvars.append({'device':DV.DeviceName,'table':table,'tag':datagram['names'][i],'type':type,'label':CustomLabel,'extrapolate':''})
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