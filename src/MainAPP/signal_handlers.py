from django.dispatch import receiver
import logging
logger = logging.getLogger("project")
from .models import AutomationVariables
import DevicesAPP.signals

@receiver(DevicesAPP.signals.SignalVariableValueUpdated, dispatch_uid="SignalVariableValueUpdated_MainAPP_receiver")
def AutomationVariablesValueUpdated_handler(sender, **kwargs):
    timestamp=kwargs['timestamp']
    Tags=kwargs['Tags']
    Values=kwargs['Values']
    for Tag in Tags:
        try:
            AVAR=AutomationVariables.objects.get(Tag=Tag)
            AVAR.executeAutomationRules()
        except:
            pass
