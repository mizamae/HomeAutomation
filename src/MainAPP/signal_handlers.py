from django.dispatch import receiver
from channels import Group
import json

import logging
logger = logging.getLogger("project")
from .models import AutomationVariables,Thermostats
import DevicesAPP.signals

@receiver(DevicesAPP.signals.SignalVariableValueUpdated, dispatch_uid="SignalVariableValueUpdated_MainAPP_receiver")
def AutomationVariablesValueUpdated_handler(sender, **kwargs):
    from utils.dataMangling import localizeTimestamp,checkBit
    from DevicesAPP.constants import DTYPE_DIGITAL
    timestamp=localizeTimestamp(timestamp=kwargs['timestamp'])
    Tags=kwargs['Tags']
    Values=kwargs['Values']
    Types=kwargs['Types']
    DataTypes=kwargs['DataTypes']
        
    for i,Tag in enumerate(Tags):
        try:
            AVARs=[]
            if sender:  # if sender is not None, a device is sending 
                if Types[i]==DTYPE_DIGITAL:
                    AVARs=AutomationVariables.objects.filter(Tag=Tag,Device=sender)
                else:
                    AVAR=AutomationVariables.objects.get(Tag=Tag,Device=sender)
                    AVARs.append(AVAR)
            else:
                AVAR=AutomationVariables.objects.get(Tag=Tag)
                AVARs.append(AVAR)
            for k,AVAR in enumerate(AVARs):
                if Types[i]==DTYPE_DIGITAL:
                    value=checkBit(number=Values[i],position=k)
                else:
                    value=Values[i]
                AVAR.executeAutomationRules()
                Group('AVAR-values').send({'text':json.dumps({'Timestamp': timestamp.strftime("%d %B %Y %H:%M:%S"),'pk':AVAR.pk,
                                                              'Label':AVAR.Label,'Value':value,'Type':DataTypes[i],'Tendency':AVAR.Tendency})},
                                          immediately=True)
                AVAR.checkAdditionalCalculations()
                
                AVAR.setTendency()
        except Exception as exc:
            logger("Error on signals: " + str(exc))

@receiver(DevicesAPP.signals.SignalNewDataFromDevice, dispatch_uid="SignalNewDataFromDevice_MainAPP_receiver")
def NewDataFromDevice_handler(sender, **kwargs):
    DV=kwargs['DV']
    DG=kwargs['DG']
    Tags=DG.getStructure()['names']
    for Tag in Tags:
        try:
            AVAR=AutomationVariables.objects.get(Tag=Tag,Device=DV.pk)
            AVAR.checkAdditionalCalculations()
        except Exception as exc:
            logger("Error on signals: " + str(exc))
    