
import logging
logger = logging.getLogger("project")
from .models import AutomationVariables

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
