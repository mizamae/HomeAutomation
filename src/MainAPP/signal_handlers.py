from django.dispatch import receiver
from channels import Group
import json

import logging
logger = logging.getLogger("project")
from .models import AutomationVariables
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
            Group('AVAR-values').send({'text':json.dumps({'Timestamp': timestamp.strftime("%d %B %Y %H:%M:%S"),
                                                          'Label':AVAR.Label,'Value':Values[i],'Type':Types[i]})},
                                      immediately=True)
        except:
            pass
