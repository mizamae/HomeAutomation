from django.dispatch import receiver
from channels import Group
import json

import logging
logger = logging.getLogger("project")
from .models import AutomationVariables,Thermostats
import DevicesAPP.signals
from DevicesAPP.constants import DTYPE_DIGITAL
from utils.dataMangling import localizeTimestamp,checkBit

@receiver(DevicesAPP.signals.SignalVariableValueUpdated, dispatch_uid="SignalVariableValueUpdated_MainAPP_receiver")
def AutomationVariablesValueUpdated_handler(sender, **kwargs):
    
    
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
                if Values[i]!=None:
                    if Types[i]==DTYPE_DIGITAL:
                        value=1 if checkBit(number=Values[i],position=k) else 0
                        AVAR.calculateDuty()
                    else:
                        value=Values[i]
                    AVAR.executeAutomationRules()
                    Group('AVAR-values').send({'text':json.dumps({'Timestamp': timestamp.strftime("%d %B %Y %H:%M:%S"),'pk':AVAR.pk,
                                                                  'Label':AVAR.Label,'Value':value,'Type':DataTypes[i],'Tendency':AVAR.Tendency})},
                                              immediately=True)
                    AVAR.checkAdditionalCalculations()
                    
                    AVAR.setTendency()
        except Exception as exc:
            logger.error("Error on signals: " + str(exc))

@receiver(DevicesAPP.signals.SignalNewDataFromDevice, dispatch_uid="SignalNewDataFromDevice_MainAPP_receiver")
def NewDataFromDevice_handler(sender, **kwargs):
    DV=kwargs['DV']
    DG=kwargs['DG']
    structure=DG.getStructure()
    Tags=structure['names']
    Types=structure['types']
    for i,Tag in enumerate(Tags):
        try:
            AVARs=[]
            if Types[i]==DTYPE_DIGITAL:
                AVARs=AutomationVariables.objects.filter(Tag=Tag,Device=DV.pk)
            else:
                AVAR=AutomationVariables.objects.get(Tag=Tag,Device=DV.pk)
                AVARs.append(AVAR)
            for AVAR in AVARs:
                AVAR.checkAdditionalCalculations()
        except Exception as exc:
            logger.error("Error on signals: " + str(exc))
    