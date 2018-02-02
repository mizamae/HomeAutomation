from django.apps import AppConfig
import sys
import os
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _

import logging
logger = logging.getLogger("processes")

from .constants import BOOTING_MSG

class ReportingAppConfig(AppConfig):
    name = 'ReportingAPP'
    verbose_name = _('Reporting APP')
    
    def ready(self):
        process=os.getpid()
        import DevicesAPP.signals
        if cache.get(self.name)==None:
            cache.set(self.name, process, 40)
            # signals are imported, so that they are defined and can be used
            # import Devices.BBDD
            # import Devices.GlobalVars
            # registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                       # configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')
                                       
            #logger.info('Start checking Registers DB on process ' + str(os.getpid()))
            #registerDB.check_IOsTables()
            #registerDB.check_registersDB()
            #logger.info('Finished checking Registers DB on process ' + str(os.getpid()))
            
        singletaskingProcess=cache.get('single_tasking')
        
        if 'gunicorn' in sys.argv[0]:
            if singletaskingProcess==None:
                cache.set('single_tasking', process, 40)
                logger.info(BOOTING_MSG)
                logger.info('SingletaskingProcess= ' + str(process) + '!!!!!!!!!!') 
                singletaskingProcess=int(process)
            else:
                singletaskingProcess=int(singletaskingProcess)

                
class ReportingAppException(Exception):
    def __name__(self):
        return 'ReportingAppException'
    pass
               