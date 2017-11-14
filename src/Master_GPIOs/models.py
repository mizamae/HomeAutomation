from django.db.models import Q
from django.db import models
from channels.binding.websockets import WebsocketBinding
from django.dispatch import receiver
from django.db.models.signals import post_save,post_delete
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.db.models import Q
import HomeAutomation.models
import RPi.GPIO as GPIO
import Master_GPIOs.signals
import Devices.BBDD
import Devices.GlobalVars
from time import sleep
import os

import logging
logger = logging.getLogger("project")

#set up GPIO using BCM numbering
GPIO.setmode(GPIO.BCM)

def initializeIOs(declareInputEvent=True):
    IOs=IOmodel.objects.all()
    logger.info("There are " + str(len(IOs))+" IOs configured")
    if len(IOs):
        logger.info("Initializing IOs from DB")
        for IO in IOs:
            if IO.direction=='OUT':
                GPIO.setup(int(IO.pin), GPIO.OUT)
                GPIO.output(int(IO.pin),IO.value)
                logger.info("   - Initialized Output on pin " + str(IO.pin))
            elif IO.direction=='IN':
                if declareInputEvent:
                    GPIO.remove_event_detect(int(IO.pin))
                    GPIO.setup(int(IO.pin), GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
                    GPIO.add_event_detect(int(IO.pin), GPIO.BOTH, callback=IO.InputChangeEvent, bouncetime=200)
                    IO.value=GPIO.input(int(IO.pin))
                    IO.save()
                else:
                    GPIO.remove_event_detect(int(IO.pin))
                    GPIO.setup(int(IO.pin), GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
                    
                logger.info("   - Initialized Input on pin " + str(IO.pin))
            IO.save()
                
class IOmodelManager(models.Manager):
    def create_IO(self, pin,label,direction,default=0,value=0):
        IO = self.create(pin=pin,label=label,direction=direction,default=default,value=value)
        IO.save()
    
class IOmodel(models.Model):
    DIRECTION_CHOICES=(
        ('OUT',_('Output')),
        ('IN',_('Input')),
        ('SENS',_('Sensor')),
    )
    VALUE_CHOICES=(
        (0,_('LOW')),
        (1,_('HIGH')),
    )
    pin = models.IntegerField(primary_key=True,unique=True)
    label = models.CharField(max_length=50,unique=True)
    direction = models.CharField(max_length=4,choices=DIRECTION_CHOICES)
    default = models.IntegerField(default=0,choices=VALUE_CHOICES)
    value = models.IntegerField(default=0,choices=VALUE_CHOICES)
    
    objects = IOmodelManager()
    
    def InputChangeEvent(self,*args):
        #sleep(0.1) # to avoid reading the input during the debounce time
        # if GPIO.gpio_function(self.pin)!=GPIO.IN:
            # GPIO.setup(self.pin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
        val=GPIO.input(self.pin)
        Master_GPIOs.signals.IN_change_notification.send(sender=None, number=self.pin, value=val)
    
    def updateAutomationVars(self):
        if self.direction=='IN':
            table='inputs'
        elif self.direction=='OUT':
            table='outputs'
        else:
            return
        AutomationVars=HomeAutomation.models.AutomationVariablesModel.objects.filter(Device='Main')
        
        dvar={'Label':self.label,'Tag':str(self.pk),'Device':'Main','Table':table,'BitPos':None}
        try:
            avar=AutomationVars.get(Tag=dvar['Tag'],Table=dvar['Table'],BitPos=dvar['BitPos'])
        except:
            avar=None
            
        if avar!=None:
            avar.Label=dvar['Label']
        else:
            avar=HomeAutomation.models.AutomationVariablesModel()
            avar.Label=dvar['Label']
            avar.Device=dvar['Device']
            avar.Tag=dvar['Tag']
            avar.Table=dvar['Table']
            avar.BitPos=dvar['BitPos']
        avar.save()
    
    def deleteAutomationVars(self):
        if self.direction=='IN':
            table='inputs'
        elif self.direction=='OUT':
            table='outputs'
        else:
            return
        avar=HomeAutomation.models.AutomationVariablesModel.objects.get(Device='Main',Tag=str(self.pk),Table=table)
        avar.delete()
        
    def __str__(self):
        return self.label + ' on pin ' + str(self.pin)
        
    class Meta:
        verbose_name = _('Input/Output')
        verbose_name_plural = _('Inputs/Outputs')

@receiver(post_save, sender=IOmodel, dispatch_uid="update_IOmodel")
def update_IOmodel(sender, instance, update_fields,**kwargs):
    registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                           configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')
    timestamp=timezone.now() #para hora con info UTC

    if kwargs['created']:   # new instance is created  
        registerDB.check_IOsTables()
        logger.info('The IO ' + str(instance) + ' has been registered on the process ' + str(os.getpid()))
        if instance.direction=='OUT':
            GPIO.setup(int(instance.pin), GPIO.OUT)
            if instance.value==1:
                GPIO.output(int(instance.pin),GPIO.HIGH)
            logger.info("Initialized Output on pin " + str(instance.pin))
            registerDB.insert_IOs_register(TimeStamp=timestamp,direction='OUT')
        elif instance.direction=='IN':
            GPIO.setup(int(instance.pin), GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
            GPIO.remove_event_detect(int(instance.pin))
            GPIO.add_event_detect(int(instance.pin), GPIO.BOTH, callback=instance.InputChangeEvent, bouncetime=200)  
            logger.info("Initialized Input on pin " + str(instance.pin))
    else:
        if instance.direction=='OUT':
            GPIO.setup(int(instance.pin), GPIO.OUT)
            if instance.value==1:
                GPIO.output(int(instance.pin),GPIO.HIGH)
            else:
                GPIO.output(int(instance.pin),GPIO.LOW)
            registerDB.insert_IOs_register(TimeStamp=timestamp,direction='OUT')

    if instance.direction!='SENS':
        instance.updateAutomationVars()
        rules=HomeAutomation.models.AutomationRuleModel.objects.filter((Q(Var1__Tag=instance.pk) & Q(Var1__Device='Main')) | (Q(Var2__Tag=instance.pk) & Q(Var2__Device='Main')))
        if len(rules)>0:
            for rule in rules:
                rule.execute()

@receiver(post_delete, sender=IOmodel, dispatch_uid="delete_IOmodel")
def delete_IOmodel(sender, instance,**kwargs):
    instance.deleteAutomationVars()
    logger.info('Se ha eliminado la IO ' + str(instance))
        
def getIOVariables(self):
    DeviceVars=[]
    IOs=IOmodel.objects.filter(Q(direction='IN') | Q(direction='OUT'))
        
    for io in IOs:
        if io.direction=='IN':
            table='inputs'
        else:
            table='outputs'
        DeviceVars.append({'Label':io.label,'Tag':str(io.pk),'Device':'Main','Table':table,'BitPos':None})
    return DeviceVars        

# def InputChangeEvent(gpio_id):
    # val=GPIO.input(gpio_id)
    # Master_GPIOs.signals.IN_change_notification.send(sender=None, number=gpio_id, value=val)
        
class IOmodelBinding(WebsocketBinding):

    model = IOmodel
    stream = "GPIO_values"
    fields = ["pin","label","direction","value"]

    @classmethod
    def group_names(cls, *args, **kwargs):
        return ["GPIO-values",]

    def has_permission(self, user, action, pk):
        return True