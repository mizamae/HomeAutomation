from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from django.dispatch import receiver
from django.db.models.signals import post_save,post_delete,pre_delete
from django.db.models.signals import m2m_changed


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
        ('REMOTE','REMOTE')
    )
    Code = models.CharField(help_text='Type of the device', max_length=10,primary_key=True)
    Description = models.CharField(help_text='Description of the device', max_length=50)
    MinSampletime=models.PositiveIntegerField(default=10)
    Connection= models.CharField(help_text='Connection of the device',choices=CONNECTION_CHOICES, max_length=15)
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
        
class DigitalItemModel(models.Model):
    DBTag = models.CharField(max_length=25,blank = True,editable=False,null=True)
    HumanTag = models.CharField(max_length=20,unique=True)
    
    def clean(self):
        ' some non-utf-8 characters might be inserted so they need to be taken care of'
        self.DBTag=self.HumanTag.replace(' ','_')+'_[bits]'
    
    def getText(self):
        return self.HumanTag+'_'+'bits'
        
    def __str__(self):
        return self.HumanTag
        
    class Meta:
        verbose_name = _('Digital field')
        verbose_name_plural = _('Digital fields')
        
class AnalogItemModel(models.Model):
    DATATYPE_CHOICES=(
        ('INTEGER','Integer'),
        ('FLOAT','Float')
    )
    DBTag = models.CharField(max_length=33,blank = True,editable=False,null=True)
    HumanTag = models.CharField(max_length=20,unique=True)
    DataType= models.CharField(max_length=10,choices=DATATYPE_CHOICES)
    Units = models.CharField(max_length=10)
    
    def clean(self):
        self.DBTag=self.HumanTag.replace(' ','_')+'_['+self.Units+']'
                        
    def __str__(self):
        return self.HumanTag
        
    class Meta:
        verbose_name = _('Analog field')
        verbose_name_plural = _('Analog fields')
        
class DatagramModel(models.Model):
    DATAGRAMTYPE_CHOICES=(
        ('Synchronous','Synchronous'),
        ('Asynchronous','Asynchronous')
    )
    Identifier = models.CharField(max_length=20)
    Code= models.PositiveSmallIntegerField(help_text='Identifier byte-type code')
    Type= models.CharField(max_length=12,choices=DATAGRAMTYPE_CHOICES)
    DeviceType = models.ForeignKey(DeviceTypeModel,on_delete=models.CASCADE)
    AnItems = models.ManyToManyField(AnalogItemModel, through='ItemOrdering',blank=True)#
    DgItems = models.ManyToManyField(DigitalItemModel,through='ItemOrdering',blank=True)
    def __str__(self):
        return self.Identifier
    
    def clean(self):
        pass
        
    def isSynchronous(self):
        return self.Type=='Synchronous'
    
    def get_variables(self):
        variables=[]
        for item in self.itemordering_set.all():
            if item.AnItem!= None:
                variables.insert(item.order,item.AnItem.HumanTag)
                logger.info('Item ' + str(item.order) + ' - ' + str(item.AnItem))
            else:
                variables.insert(item.order,item.DgItem.HumanTag)
                logger.info('Item ' + str(item.order) + ' - ' + str(item.DgItem))
        return variables
    
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
        logger.info('Tiene ' + str(instance.AnItems.count())+' ' + (AnalogItemModel._meta.verbose_name.title() if (instance.AnItems.count()==1) else AnalogItemModel._meta.verbose_name_plural.title()))
        for analog in instance.AnItems.all():
            logger.info('   - ' + str(analog.HumanTag))
        logger.info('Tiene ' + str(instance.DgItems.count())+' ' + (DigitalItemModel._meta.verbose_name.title() if (instance.DgItems.count()==1) else DigitalItemModel._meta.verbose_name_plural.title()))
        for digital in instance.DgItems.all():
            logger.info('   - ' + str(digital.HumanTag))
    instance.get_variables()

def getDatagramStructure(devicetype,ID='*'):
    if ID=='*':
        datagrams=DatagramModel.objects.filter(DeviceType=devicetype)
    else:
        datagrams=DatagramModel.objects.filter(DeviceType=devicetype,Identifier=ID)
    datagramList=[]
    
    for datagram in datagrams:
        names=[]
        types=[]
        datatypes=[]
        datagramID=datagram.Identifier
        analogItems=datagram.AnItems.all()
        for item in analogItems:
            Itemorder=ItemOrdering.objects.get(AnItem=item,datagram=datagram)
            names.insert(Itemorder.order,Itemorder.AnItem.HumanTag+'_'+Itemorder.AnItem.Units)
            datatypes.insert(Itemorder.order,Itemorder.AnItem.DataType)
            types.insert(Itemorder.order,'analog')
        digitalItems=datagram.DgItems.all()
        for item in digitalItems:
            Itemorder=ItemOrdering.objects.get(DgItem=item,datagram=datagram)
            names.insert(Itemorder.order,Itemorder.DgItem.getText())
            datatypes.insert(Itemorder.order,'INTEGER')
            types.insert(Itemorder.order,'digital')
        if datagram.isSynchronous():
            sample=1
        else:
            sample=0
        
        datagramList.append({'ID':datagramID,'names':names,'types':types,'datatypes':datatypes,'sample':sample})
        #logger.info('getDatagramStructure: '+ str(datagramList)) 
        
    if ID =='*':
        #logger.info('getDatagramStructure: '+ str(datagramList))
        return datagramList
    else:
        return datagramList[0]

def getAllVariables():
    import Master_GPIOs.models 
    import LocalDevices.models 
    import RemoteDevices.models 
    import HomeAutomation.models
    import json
    import itertools
    
    info=[]
    RDVs=RemoteDevices.models.DeviceModel.objects.all()
    LDVs=LocalDevices.models.DeviceModel.objects.all()
    DVs=[RDVs,LDVs]
    IOs=Master_GPIOs.models.IOmodel.objects.all()
    MainVars=HomeAutomation.models.MainDeviceVarModel.objects.all()
    tempvars=[]
    if len(IOs)>0:
        for IO in IOs:
            if IO.direction=='IN' or IO.direction=='OUT':
                if IO.direction=='IN':
                    table='inputs'
                else:
                    table='outputs'
                tempvars.append({'device':'Main','table':table,'tag':str(IO.pin),# this is to tell the template that it is a boolean value
                                'label':[IO.label,],'extrapolate':'keepPrevious','type':'digital'})
                                
        info.append({'deviceName':'Main','variables':tempvars})
    tempvars=[]
    if len(MainVars)>0:
        for VAR in MainVars:
            table='MainVariables'
            tempvars.append({'device':'Main','table':table,'tag':str(VAR.pk),# this is to tell the template that it is a boolean value
                            'label':VAR.Label,'extrapolate':'keepPrevious','type':'analog'})
                                
        info.append({'deviceName':'Main','variables':tempvars})
        
    for device in itertools.chain(*DVs):    # device[0]= DeviceName, device[1]=DeviceType  
        DEVICE_TYPE=str(device.Type.Code)
        datagrams=getDatagramStructure(devicetype=DEVICE_TYPE)#XMLParser.getDatagramsStructureForDeviceType(deviceType=DEVICE_TYPE)
        tempvars=[]
        for datagram in datagrams: 
            table=device.DeviceName+'_'+datagram['ID']
            labels=[]
            if device.CustomLabels!='':
                CustomLabels=json.loads(device.CustomLabels)
                labels=CustomLabels[datagram['ID']]
                Labeliterable=labels
            else:
                Labeliterable=datagram['names']
            for i,var in enumerate(Labeliterable):                     
                CustomLabel='' 
                type=datagram['types'][i]
                if type=='digital':                                                          
                    if str(var).find('$')>=0:
                        try:
                            CustomLabel=str(var).split('_')[-1].split('$')
                        except:
                            CustomLabel=''
                        pos=str(var).lower().find('_bits')
                        var=var[0:pos+5]
                else:
                    CustomLabel=var.replace('_',' [')+']'
                if (str(var).lower()!='spare') and (str(var).lower()!='timestamp'):                                       
                    tempvars.append({'device':device.DeviceName,'table':table,'tag':datagram['names'][i],'type':type,'label':CustomLabel,'extrapolate':''})
        info.append({'deviceName':device.DeviceName,'variables':tempvars})
    return info
    
class ItemOrdering(models.Model):
    datagram = models.ForeignKey(DatagramModel, on_delete=models.CASCADE)
    AnItem = models.ForeignKey(AnalogItemModel, on_delete=models.CASCADE,blank=True,null=True)
    DgItem = models.ForeignKey(DigitalItemModel, on_delete=models.CASCADE,blank=True,null=True)
    order = models.PositiveSmallIntegerField(help_text='Position in the dataframe 1-based')
    
    def __str__(self):
        return str(self.datagram) + ':' +str(self.order)
        
    class Meta:
        unique_together = ('order', 'datagram')
        verbose_name = _('Item')
        verbose_name_plural = _('Items')
        ordering = ('order',)

# these Signal functions are not triggered due to a Django bug https://code.djangoproject.com/ticket/16073
def AnItems_changed(sender,instance, action, **kwargs):
    logger.info('Ahora tiene ' + str(instance.AnItems.count())+' ' + (AnalogItemModel._meta.verbose_name.title() if (instance.AnItems.count()==1) else AnalogItemModel._meta.verbose_name_plural.title()))
    for analog in instance.AnItems.all():
        logger.info('   - ' + str(analog.HumanTag))
    
def DgItems_changed(sebder,instance, action,**kwargs):
    logger.info('Ahora tiene ' + str(instance.DgItems.count())+' ' + (DigitalItemModel._meta.verbose_name.title() if (instance.DgItems.count()==1) else DigitalItemModel._meta.verbose_name_plural.title()))
    for digital in instance.DgItems.all():
        logger.info('   - ' + str(digital.HumanTag))
m2m_changed.connect(AnItems_changed, sender=DatagramModel.AnItems.through,weak=False)
m2m_changed.connect(DgItems_changed, sender=DatagramModel.DgItems.through,weak=False)

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