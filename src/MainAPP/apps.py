from django.apps import AppConfig
import sys
import logging
import os
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger("processes")

# with this initialization we guarantee that only one process will have the imanagement tasks scheduled.

from .constants import BOOTING_MSG
                
class AutomationConfig(AppConfig):
    name = 'MainAPP'
    verbose_name = _('Automation APP')
    
    def ready(self):
        process=os.getpid()
        import MainAPP.signal_handlers
        logger.debug('Process init: ' + str(os.getpid()) + '('+str(sys.argv[0])+ ')')
        import MainAPP.tasks
        logger.debug('Process '+str(process) + ' is a Gunicorn process')
        MainAPP.tasks.start_registersDBcompactingTask()
        MainAPP.tasks.start_DailyTask()
        MainAPP.tasks.start_HourlyTask()
        logger.info('Initializing management tasks on the process ' + str(os.getpid()))