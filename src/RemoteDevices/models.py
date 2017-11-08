from django.db import models
from django.utils.translation import ugettext_lazy as _

from django.dispatch import receiver
from django.db.models.signals import post_save,post_delete

from channels.binding.websockets import WebsocketBinding

import Devices.XML_parser
import Devices.GlobalVars
import Devices.BBDD
import Devices.models
import HomeAutomation.models
import json

import RemoteDevices.signals
import xml.etree.ElementTree as ET
import logging
import datetime
logger = logging.getLogger("project")
#replace print by logger.info

xmlroot = ET.parse(Devices.GlobalVars.XML_CONFFILE_PATH).getroot()
XMLParser=Devices.XML_parser.XMLParser(xmlroot=xmlroot)
DEVICE_TYPES=XMLParser.getDeviceTypesConfFile()
DEVICE_TYPE_CHOICES=[]
for device in DEVICE_TYPES:
    DEVICE_TYPE_CHOICES.append((device,device))
    
class DeviceModelManager(models.Manager):
    def create_Device(self, DeviceName,DeviceCode,DeviceIP,DeviceType,DeviceState,Sampletime,LastUpdated='1981-11-27',DeviceHTTPCode=0,Error=''):
        if LastUpdated=='1981-11-27':
            LastUpdated=datetime.datetime.now()
        Dev = self.create(DeviceName=DeviceName,DeviceCode=DeviceCode,DeviceIP=DeviceIP,Type=DeviceType,DeviceState='STOPPED',Sampletime=Sampletime,LastUpdated=LastUpdated,
                          DeviceHTTPCode=DeviceHTTPCode,Error=Error)
        Dev.save()

class DeviceModel(models.Model):
    
    STATE_CHOICES=(
        ('STOPPED','STOPPED'),
        ('RUNNING','RUNNING')
    )
    __original_DeviceName = None
    
    DeviceName = models.CharField(max_length=20,unique=True,error_messages={'unique':_("Invalid device name - This name already exists in the DB.")})
    DeviceCode = models.IntegerField(unique=True,error_messages={'unique':_("Invalid device code - This code already exists in the DB.")})
    DeviceIP = models.GenericIPAddressField(protocol='IPv4', unique=True,error_messages={'unique':_("Invalid IP - This IP already exists in the DB.")})
    Type = models.ForeignKey('Devices.DeviceTypeModel',related_name="Remote",on_delete=models.CASCADE,limit_choices_to={'Connection': 'REMOTE'})
    DeviceState = models.CharField(choices=STATE_CHOICES, max_length=15)
    Sampletime= models.IntegerField(default=60)
    LastUpdated = models.DateTimeField(blank = True,null=True)
    DeviceHTTPCode = models.IntegerField(blank = True,editable=False,null=True)  # gathers the HTTP response code from the device 200=OK
    Error=models.CharField(max_length=100,blank = True,editable=False,null=True)
    CustomLabels = models.CharField(max_length=1500,default='',blank=True) # json string containing the user-defined labels for each of the items in the datagrams
    
    objects = DeviceModelManager()
        
    def __str__(self):
        return self.DeviceName
    
    def __init__(self, *args, **kwargs):
        super(DeviceModel, self).__init__(*args, **kwargs)
        self.__original_DeviceName = self.DeviceName
    
    def save(self, *args, **kwargs):
        if self.DeviceName != self.__original_DeviceName and self.__original_DeviceName != '':
             RemoteDevices.signals.DeviceName_changed.send(sender=None, OldDeviceName=self.__original_DeviceName,NewDeviceName=self.DeviceName)
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
        verbose_name = _('Device')
        verbose_name_plural = _('Devices')

@receiver(post_save, sender=DeviceModel, dispatch_uid="update_RemoteDeviceModel")
def update_DeviceModel(sender, instance, update_fields,**kwargs):
    if kwargs['created']:   # new instance is created
        registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                           configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')
        registerDB.create_DeviceRegistersTables(DeviceName=instance.DeviceName,DeviceType=instance.Type.Code)
        print('Se ha registrado el dispositivo ' + str(instance) +' del tipo ' + str(instance.Type.Code))
    instance.updateAutomationVars()
      
@receiver(post_delete, sender=DeviceModel, dispatch_uid="delete_RemoteDeviceModel")
def delete_DeviceModel(sender, instance,**kwargs):
    instance.deleteAutomationVars()
    logger.info('Se ha eliminado el dispositivo ' + str(instance))
    # applicationDBs=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                      # configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH)   
    # applicationDBs.delete_DeviceRegister_tables(DeviceName=instance.DeviceName)

class DeviceModelBinding(WebsocketBinding):

    model = DeviceModel
    stream = "RDevice_params"
    fields = ["DeviceName","DeviceCode","DeviceIP","Type","Sampletime","DeviceState","LastUpdated","DeviceHTTPCode"]

    @classmethod
    def group_names(cls, *args, **kwargs):
        return ["Device-models",]

    def has_permission(self, user, action, pk):
        return True
        