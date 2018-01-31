from django.apps import AppConfig
import sys
import logging
import os
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger("processes")

# with this initialization we guarantee that only one process will have the imanagement tasks scheduled.

from .constants import BOOTING_MSG
                
class HomeAutomationConfig(AppConfig):
    name = 'HomeAutomation'
    verbose_name = _('HomeAutomation base app')
    
    def ready(self):
        process=os.getpid()
        logger.debug('Process init: ' + str(os.getpid()) + '('+str(sys.argv[0])+ ')')
        import HomeAutomation.tasks
        logger.debug('Process '+str(process) + ' is a Gunicorn process')
        HomeAutomation.tasks.start_registersDBcompactingTask()
        HomeAutomation.tasks.start_DailyTask()
        HomeAutomation.tasks.start_HourlyTask()
        logger.info('Initializing management tasks on the process ' + str(os.getpid()))
            