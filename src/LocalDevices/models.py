from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver
from django.db.models.signals import post_save,post_delete
from django.core.validators import MinValueValidator

from channels.binding.websockets import WebsocketBinding
from Master_GPIOs.models import IOmodel
import Devices.GlobalVars
import Devices.BBDD
import Devices.models
import HomeAutomation.models
import json

#import LocalDevices.signals #raises error when importing this

import logging

logger = logging.getLogger("project")
        
class DeviceModelManager(models.Manager):
    def create_Device(self, DeviceName,DeviceCode,DeviceIP,DeviceType,DeviceState,LastUpdated='1981-11-27',DeviceHTTPCode=0,Error=''):
        Dev = self.create(DeviceName=DeviceName,DeviceCode=DeviceCode,DeviceIP=DeviceIP,DeviceState=DeviceState,LastUpdated=LastUpdated,
                          DeviceHTTPCode=DeviceHTTPCode,Error=Error)
        Dev.save()

class DeviceModel(models.Model):
    
    STATE_CHOICES=(
        ('STOPPED','STOPPED'),
        ('RUNNING','RUNNING')
    )
    
    __original_DeviceName = None
    
    DeviceName = models.CharField(help_text='Name for the device', max_length=20,unique=True,error_messages={'unique':_("Invalid device name - This name already exists in the DB.")})
    IO = models.OneToOneField(IOmodel,on_delete=models.CASCADE,primary_key=True)
    Type = models.ForeignKey('Devices.DeviceTypeModel',related_name="Local",on_delete=models.CASCADE,limit_choices_to={'Connection': 'LOCAL'})
    DeviceState= models.CharField(help_text='State of the device',choices=STATE_CHOICES, max_length=15)
    Sampletime=models.PositiveIntegerField(default=600)
    RTsampletime=models.PositiveIntegerField(default=600)
    LastUpdated= models.DateTimeField(help_text='Datetime of the last data',blank = True,null=True)
    Connected = models.BooleanField(default=False)  # defines if the device is properly detected and transmits OK
    CustomLabels = models.CharField(max_length=1500,default='',blank=True) # json string containing the user-defined labels for each of the items in the datagrams
    
    objects = DeviceModelManager()
    
    def clean(self):
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
        
    def getDeviceVariables(self):
        DeviceVars=[]
        datagrams=Devices.models.getDatagramStructure(devicetype=self.Type,ID='*')
        if self.CustomLabels!='':
            CustomLabels=json.loads(self.CustomLabels)
        else:
            CustomLabels=None
            
        for datagram in datagrams:
            datagramID=datagram['ID']
            Vars=datagram['names']
            Types=datagram['types']
            if CustomLabels!=None:
                CustomVars=CustomLabels[datagramID]
            else:
                CustomVars=datagram['names']
                
            for cvar,var,type in zip(CustomVars,Vars,Types):
                if type=='digital':
                    BitLabels=cvar.split('$')
                    for i,bitLabel in enumerate(BitLabels):
                        DeviceVars.append({'Label':bitLabel,'Tag':var,'Device':self.DeviceName,'Table':self.DeviceName+'_'+datagramID,'BitPos':i,'Sample':datagram['sample']*self.Sampletime})
                else:
                    DeviceVars.append({'Label':cvar,'Tag':var,'Device':self.DeviceName,'Table':self.DeviceName+'_'+datagramID,'BitPos':None,'Sample':datagram['sample']*self.Sampletime})
        return DeviceVars
    
    def updateAutomationVars(self):
        AutomationVars=HomeAutomation.models.AutomationVariablesModel.objects.filter(Device=self.DeviceName)
        DeviceVars=self.getDeviceVariables()
        for dvar in DeviceVars:
            try:
                avar=AutomationVars.get(Tag=dvar['Tag'],Table=dvar['Table'],BitPos=dvar['BitPos'])
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
        verbose_name = _('Local device')
        verbose_name_plural = _('Local devices')
        
@receiver(post_save, sender=DeviceModel, dispatch_uid="update_LocalDeviceModel")
def update_DeviceModel(sender, instance, update_fields,**kwargs):
        
    if kwargs['created']:   # new instance is created
        registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                           configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')
        
        registerDB.create_DeviceRegistersTables(DeviceName=instance.DeviceName,DeviceType=instance.Type.Code)
    else:
        instance.updateAutomationVars()
        
@receiver(post_delete, sender=DeviceModel, dispatch_uid="delete_LocalDeviceModel")
def delete_DeviceModel(sender, instance,**kwargs):
    instance.deleteAutomationVars()
    logger.info('Se ha eliminado el dispositivo ' + str(instance))

# def clean(self):
#         # Only allow one instance of Camera model
#         validate_only_one_instance(self)

class DeviceModelBinding(WebsocketBinding):

    model = DeviceModel
    stream = "LDevice_params"
    fields = ["DeviceName","IO","Type","DeviceState","Sampletime","LastUpdated","Connected"]

    @classmethod
    def group_names(cls, *args, **kwargs):
        return ["Device-models",]

    def has_permission(self, user, action, pk):
        return True
        
def validate_only_one_instance(object):
    """
    Validate that only one instance of a model exists.
    """
    model = object.__class__
    if (model.objects.count() > 0 and object.id != model.objects.get().id):
        raise ValidationError('Only one instance of model %s allowed.' % model.__name__)

