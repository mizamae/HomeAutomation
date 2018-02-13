from django.dispatch import receiver

import logging
logger = logging.getLogger("project")

from .models import MasterGPIOs
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
