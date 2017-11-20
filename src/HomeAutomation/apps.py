from django.apps import AppConfig
import sys
    
import logging
import os
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger("processes")

# with this initialization we guarantee that only one process will have the imanagement tasks scheduled.

from Devices.GlobalVars import BOOTING_MSG

# for process in psutil.process_iter():
#     cmdline = process.cmdline
#     if 'python' in cmdline:
#         print(str(cmdline))                

    
    
class HomeAutomationConfig(AppConfig):
    name = 'HomeAutomation'
    verbose_name = _('HomeAutomation base app')
    
    def ready(self):
        process=os.getpid()
        if 'python' in sys.argv:
            print(str(sys.argv))  
             
        if cache.get(self.name)==None:
            managementProcess=cache.get('management_tasking')
            singletaskingProcess=cache.get('single_tasking')
            if singletaskingProcess!=None:
                singletaskingProcess=int(singletaskingProcess)
            else:
                singletaskingProcess=0
                
            if managementProcess==None and singletaskingProcess!=int(process):
                cache.set('management_tasking', process, 60)
                logger.info(BOOTING_MSG)
                logger.info('ManagementProcess= ' + str(process) + '!!!!!!!!!!')
                managementProcess=int(process)
            if managementProcess==int(process):
                cache.set(self.name, os.getpid(), 60)
                import HomeAutomation.tasks
                HomeAutomation.tasks.start_registersDBcompactingTask()
                HomeAutomation.tasks.start_reportsGenerationTask()
                HomeAutomation.tasks.start_HourlyTask()
                logger.info('Initializing management tasks on the process ' + str(os.getpid()))
        