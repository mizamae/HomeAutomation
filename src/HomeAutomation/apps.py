from django.apps import AppConfig
import sys
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
        logger.debug('Process init: ' + str(os.getpid()) + '('+str(sys.argv[0])+ ')')
        singletaskingProcess=cache.get('single_tasking')
        if singletaskingProcess==None and 'gunicorn' in sys.argv[0]:
            logger.info(BOOTING_MSG)
            logger.debug('Process '+str(process) + ' is a Gunicorn process')
            cache.set('single_tasking', process, 60)
            logger.debug('SingleTaskingProcess ' + str(process) + '!!!!')
            cache.set(self.name, process, 60)
            import HomeAutomation.tasks
            HomeAutomation.tasks.start_registersDBcompactingTask()
            HomeAutomation.tasks.start_reportsGenerationTask()
            HomeAutomation.tasks.start_HourlyTask()
            logger.info('Initializing management tasks on the process ' + str(os.getpid()))
        elif cache.get(self.name)==None and 'gunicorn' in sys.argv[0] and singletaskingProcess==int(process):
            import HomeAutomation.tasks
            logger.debug('Process '+str(process) + ' is a Gunicorn process')
            HomeAutomation.tasks.start_registersDBcompactingTask()
            HomeAutomation.tasks.start_reportsGenerationTask()
            HomeAutomation.tasks.start_HourlyTask()
            logger.info('Initializing management tasks on the process ' + str(os.getpid()))
        
                
                
            
# class HomeAutomationConfig(AppConfig):
    # name = 'HomeAutomation'
    # verbose_name = _('HomeAutomation base app')
    
    # def ready(self):
        # process=os.getpid()
        # logger.debug(str(sys.argv))
        # logger.debug('Process init: ' + str(os.getpid()))
        # if cache.get(self.name)==None:
            # singletaskingProcess=cache.get('single_tasking')
            # if singletaskingProcess==None:
                # cache.set('single_tasking', process, 60)
                # logger.info(BOOTING_MSG)
                # logger.info('SingletaskingProcess= ' + str(process) + '!!!!!!!!!!')
                # singletaskingProcess=int(process)
            # else:
                # singletaskingProcess=int(singletaskingProcess)
            # if singletaskingProcess==int(process):
                # cache.set(self.name, os.getpid(), 60)
                # import HomeAutomation.tasks
                # HomeAutomation.tasks.start_registersDBcompactingTask()
                # HomeAutomation.tasks.start_reportsGenerationTask()
                # HomeAutomation.tasks.start_HourlyTask()
                # logger.info('Initializing management tasks on the process ' + str(os.getpid()))       