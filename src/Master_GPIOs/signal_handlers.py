import Master_GPIOs.models
import RPi.GPIO as GPIO
import logging
import os
from django.utils import timezone
import datetime
import Devices.GlobalVars
import Devices.BBDD

logger = logging.getLogger("project")

def OUT_toggle_request_handler(sender, **kwargs):
    number = int(kwargs['number'])
    logger.info("Received signal to toggle output " + str(number) + " on the process " + str(os.getpid()))
    # toggle gpio number
    GPIO.setup(number, GPIO.OUT)
    value=GPIO.input(number)
    GPIO.output(number, not value)
    IO=Master_GPIOs.models.IOmodel.objects.get(pin=number)
    IO.value=GPIO.input(number)
    #logger.info("Output was "+str(value) + " and now is " + str(IO.value))
    
    timestamp=timezone.now() #para hora con info UTC
    applicationDBs=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                      configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH)
    applicationDBs.insert_IOs_register(TimeStamp=timestamp-datetime.timedelta(seconds=1),direction='OUT')
    IO.save()
    #applicationDBs.insert_event(TimeStamp=timestamp,Sender='Web: '+str(sender),DeviceName='Main',EventType=applicationDBs.EVENT_TYPES['OUTPUT_CHANGE'],value=IO.value)
    applicationDBs.insert_IOs_register(TimeStamp=timestamp,direction='OUT')
        


def IN_change_notification_handler(sender, **kwargs):
    number = int(kwargs['number'])
    value = int(kwargs['value'])
    logger.info("Received notification that the input " + str(number) + " has changed to " +str(value)+ " on the process " + str(os.getpid()))
    IO=Master_GPIOs.models.IOmodel.objects.get(pin=number)
    
    timestamp=timezone.now() #para hora con info UTC 
    applicationDBs=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                      configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH)
    applicationDBs.insert_IOs_register(TimeStamp=timestamp-datetime.timedelta(seconds=1),direction='IN')
    #applicationDBs.insert_event(TimeStamp=timestamp,Sender=str(sender),DeviceName='Main',EventType=applicationDBs.EVENT_TYPES['INPUT_CHANGE'],value=IO.value)
    IO.value=value
    IO.save()
    applicationDBs.insert_IOs_register(TimeStamp=timestamp,direction='IN')

    
