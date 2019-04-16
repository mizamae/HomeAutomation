from django.dispatch import receiver

import logging
logger = logging.getLogger("project")

from .models import MasterGPIOs,MainDeviceVars
import MainAPP.signals

from .constants import GPIO_OUTPUT,GPIO_INPUT
                        
@receiver(MainAPP.signals.SignalSetGPIO, dispatch_uid="SignalSetGPIO_DevicesAPP_receiver")
def SignalSetGPIO_handler(sender, **kwargs):
    pk=kwargs['pk']
    Value=kwargs['Value']
    IO=MasterGPIOs.objects.get(pk=pk)
    #logger.info("Received signal to set GPIO to " + str(Value))
    if IO.Direction==GPIO_OUTPUT:
        if Value==0:
            IO.setLow()
        elif Value==1:
            IO.setHigh()
    
@receiver(MainAPP.signals.SignalToggleAVAR, dispatch_uid="SignalToggleAVAR_DevicesAPP_receiver")
def SignalToggleAVAR_handler(sender, **kwargs):
    Device=kwargs['Device']
    Tag=kwargs['Tag']
    newValue=kwargs['newValue']
    force=kwargs.get('force',None)
    if Device=='MainGPIOs':
        Instance=MasterGPIOs.objects.get(pk=Tag)
    elif Device=='MainVars':
        Instance=MainDeviceVars.objects.get(pk=Tag)
    else:
        return
    Instance.toggle(newValue=newValue,force=force)
    
@receiver(MainAPP.signals.SignalCreateMainDeviceVars, dispatch_uid="SignalCreateMainDeviceVars_DevicesAPP_receiver")
def SignalCreateMainDeviceVars_handler(sender, **kwargs):
    data=kwargs['Data']
    Instance=MainDeviceVars(**data)
    try:
        Instance.store2DB()
    except Exception as exc:
        print('Error:' + str(exc))
    
@receiver(MainAPP.signals.SignalUpdateValueMainDeviceVars, dispatch_uid="SignalUpdateValueMainDeviceVars_DevicesAPP_receiver")
def SignalUpdateValueMainDeviceVars_handler(sender, **kwargs):
    Tag=kwargs['Tag']
    timestamp=kwargs['timestamp']
    newValue=kwargs['newValue']
    force=kwargs['force']
    Instance=MainDeviceVars.objects.get(pk=Tag)
    Instance.updateValue(newValue=newValue,timestamp=timestamp,writeDB=True,force=force)