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
    if IO.Direction==GPIO_OUTPUT:
        if Value==0:
            IO.setLow()
        elif Value==1:
            IO.setHigh()

@receiver(MainAPP.signals.SignalToggleAVAR, dispatch_uid="SignalToggleAVAR_DevicesAPP_receiver")
def SignalToggleAVAR_handler(sender, **kwargs):
    Device=kwargs['Device']
    Tag=kwargs['Tag']
    if Device=='MainGPIOs':
        Instance=MasterGPIOs.objects.get(pk=Tag)
    elif Device=='MainVars':
        Instance=MainDeviceVars.objects.get(pk=Tag)
    Instance.toggle()