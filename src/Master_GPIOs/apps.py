from django.apps import AppConfig

import logging
import os
import sys
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger("processes")

# with this initialization we guarantee that only one process will have the input change detection configured.
# this avoids the multiple callbacks when an input changes its value as only one process will be aware of it.

from Devices.GlobalVars import BOOTING_MSG
                
class GPIOsConfig(AppConfig):
    name = 'Master_GPIOs'
    verbose_name = _('I/Os manager')
    
    def ready(self):
        import Master_GPIOs.signals
        from Master_GPIOs.models import initializeIOs
        process=os.getpid()
        if cache.get(self.name)==None and 'gunicorn' in sys.argv[0]:
            singletaskingProcess=cache.get('single_tasking')
            if singletaskingProcess==None:
                cache.set('single_tasking', process, 40)
                logger.info(BOOTING_MSG)
                logger.info('SingletaskingProcess= ' + str(process) + '!!!!!!!!!!')
                singletaskingProcess=int(process)
            else:
                singletaskingProcess=int(singletaskingProcess)
            if singletaskingProcess==int(process):
                cache.set(self.name, os.getpid(), 40)
                logger.info('Initializing IOs inputs events on the process ' + str(os.getpid()))
                initializeIOs(declareInputEvent=True)
        else:
            initializeIOs(declareInputEvent=False)
            logger.info('Initializing IOs on the process ' + str(os.getpid()))

# class GPIOsConfig(AppConfig):
    # name = 'Master_GPIOs'
    # verbose_name = _('I/Os manager')
    
    # def ready(self):
        # import Master_GPIOs.signals
        # from Master_GPIOs.models import initializeIOs
        # process=os.getpid()
        # if cache.get(self.name)==None:
            # singletaskingProcess=cache.get('single_tasking')
            # if singletaskingProcess==None:
                # cache.set('single_tasking', process, 40)
                # logger.info(BOOTING_MSG)
                # logger.info('SingletaskingProcess= ' + str(process) + '!!!!!!!!!!')
                # singletaskingProcess=int(process)
            # else:
                # singletaskingProcess=int(singletaskingProcess)
            # if singletaskingProcess==int(process):
                # cache.set(self.name, os.getpid(), 40)
                # logger.info('Initializing IOs inputs events on the process ' + str(os.getpid()))
                # #masterGPIO.initializeIOs(declareInputEvent=True)
                # initializeIOs(declareInputEvent=True)
        # else:
            # #masterGPIO.initializeIOs(declareInputEvent=False)
            # initializeIOs(declareInputEvent=False)
            # logger.info('Finished initializing IOs on the process ' + str(os.getpid()))            
