from django.apps import AppConfig
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _
import os
import sys
import logging
logger = logging.getLogger("processes")

from Devices.GlobalVars import BOOTING_MSG

class DevicesConfig(AppConfig):
    name = 'RemoteDevices'
    verbose_name = _('Remotely connected devices')
    def ready(self):
        
        # signals are imported, so that they are defined and can be used
        import RemoteDevices.signals
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
                from Devices.Requests import initialize_polling_remote
                logger.info('Initializing polling on Remote devices for the first time on process ' + str(process))
                initialize_polling_remote()
                
# class DevicesConfig(AppConfig):
    # name = 'RemoteDevices'
    # verbose_name = _('Remotely connected devices')
    # def ready(self):
        
        # # signals are imported, so that they are defined and can be used
        # import RemoteDevices.signals
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
                # from Devices.Requests import initialize_polling_remote
                # logger.info('Initializing polling on Remote devices for the first time on process ' + str(process))
                initialize_polling_remote()