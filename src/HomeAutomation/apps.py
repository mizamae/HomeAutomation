from django.apps import AppConfig

import logging
import os
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger("processes")

# with this initialization we guarantee that only one process will have the imanagement tasks scheduled.

from Devices.GlobalVars import BOOTING_MSG
                
class HomeAutomationConfig(AppConfig):
    name = 'HomeAutomation'
    verbose_name = _('HomeAutomation base app')
    
    def ready(self):
        process=os.getpid()
        if cache.get(self.name)==None:
            singletaskingProcess=cache.get('single_tasking')
            if singletaskingProcess==None:
                cache.set('single_tasking', process, 60)
                logger.info(BOOTING_MSG)
                logger.info('SingletaskingProcess= ' + str(process) + '!!!!!!!!!!')
                singletaskingProcess=int(process)
            else:
                singletaskingProcess=int(singletaskingProcess)
            if singletaskingProcess==int(process):
                cache.set(self.name, os.getpid(), 60)
                import HomeAutomation.tasks
                HomeAutomation.tasks.start_registersDBcompactingTask()
                HomeAutomation.tasks.start_reportsGenerationTask()
                logger.info('Initializing management tasks on the process ' + str(os.getpid()))
            
        