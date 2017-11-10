from django.apps import AppConfig
import os
import sys
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _

import logging
logger = logging.getLogger("processes")

from Devices.GlobalVars import BOOTING_MSG
                
class LocalDevicesConfig(AppConfig):
    name = 'LocalDevices'
    verbose_name = _('Locally connected devices')
    def ready(self):

        # signals are imported, so that they are defined and can be used
        import LocalDevices.signals
        process=os.getpid()
        singletaskingProcess=cache.get('single_tasking')
        if cache.get(self.name)==None and 'gunicorn' in sys.argv[0]:
            if singletaskingProcess==None:
                cache.set('single_tasking', process, 40)
                logger.info(BOOTING_MSG)
                logger.info('SingletaskingProcess= ' + str(process) + '!!!!!!!!!!') 
                singletaskingProcess=int(process)
            else:
                singletaskingProcess=int(singletaskingProcess)
            if singletaskingProcess==int(process):
                cache.set(self.name, process, 40)
                from Devices.Requests import initialize_polling_local
                logger.info('Initializing polling on Local devices for the first time on process ' + str(process))
                initialize_polling_local()

# class LocalDevicesConfig(AppConfig):
    # name = 'LocalDevices'
    # verbose_name = _('Locally connected devices')
    # def ready(self):

        # # signals are imported, so that they are defined and can be used
        # import LocalDevices.signals
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
                # cache.set(self.name, process, 40)
                # from Devices.Requests import initialize_polling_local
                # logger.info('Initializing polling on Local devices for the first time on process ' + str(process))
                # initialize_polling_local()                