from django.dispatch import receiver
from channels import Group
import json

import logging
logger = logging.getLogger("project")
from .models import AutomationVariables,Thermostats
import DevicesAPP.signals

@receiver(DevicesAPP.signals.SignalVariableValueUpdated, dispatch_uid="SignalVariableValueUpdated_MainAPP_receiver")
def AutomationVariablesValueUpdated_handler(sender, **kwargs):
    from utils.dataMangling import localizeTimestamp
    timestamp=localizeTimestamp(timestamp=kwargs['timestamp'])
    Tags=kwargs['Tags']
    Values=kwargs['Values']
    Types=kwargs['Types']
    
    for i,Tag in enumerate(Tags):
        try:
            AVAR=AutomationVariables.objects.get(Tag=Tag)
            AVAR.executeAutomationRules()
            Group('AVAR-values').send({'text':json.dumps({'Timestamp': timestamp.strftime("%d %B %Y %H:%M:%S"),'pk':AVAR.pk,
                                                          'Label':AVAR.Label,'Value':Values[i],'Type':Types[i],'Tendency':AVAR.Tendency})},
                                      immediately=True)
            AVAR.checkAdditionalCalculations()
            
            THRMs=Thermostats.objects.filter(RITM__Var1=AVAR)
            for THRM in THRMs:
                THRM.setTendency()
        except:
            pass

@receiver(DevicesAPP.signals.SignalNewDataFromDevice, dispatch_uid="SignalNewDataFromDevice_MainAPP_receiver")
def NewDataFromDevice_handler(sender, **kwargs):
    DV=kwargs['DV']
    DG=kwargs['DG']
    Tags=DG.getStructure()['names']
    for Tag in Tags:
        try:
            AVAR=AutomationVariables.objects.get(Tag=Tag,Device=DV.pk)
            AVAR.checkAdditionalCalculations()
        except:
            pass
    