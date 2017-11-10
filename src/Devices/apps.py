from django.apps import AppConfig
import sys
import os
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _

import logging
logger = logging.getLogger("processes")

from Devices.GlobalVars import BOOTING_MSG

class DevicesConfig(AppConfig):
    name = 'Devices'
    verbose_name = _('Devices common')
    
    def ready(self):
        process=os.getpid()
        import Devices.signals
        if cache.get(self.name)==None:
            cache.set(self.name, process, 40)
            # signals are imported, so that they are defined and can be used
            import Devices.BBDD
            import Devices.GlobalVars
            registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                       configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')
                                       
            logger.info('Start checking Registers DB on process ' + str(os.getpid()))
            registerDB.check_IOsTables()
            registerDB.check_registersDB()
            logger.info('Finished checking Registers DB on process ' + str(os.getpid()))

# class DevicesConfig(AppConfig):
    # name = 'Devices'
    # verbose_name = _('Devices common')
    
    # def ready(self):
        # process=os.getpid()
        # import Devices.signals
        # if cache.get(self.name)==None:
            # cache.set(self.name, process, 40)
            # # signals are imported, so that they are defined and can be used
            # import Devices.BBDD
            # import Devices.GlobalVars
            # registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                       # configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')
                                       
            # logger.info('Start checking Registers DB on process ' + str(os.getpid()))
            # registerDB.check_IOsTables()
            # registerDB.check_registersDB()
            # logger.info('Finished checking Registers DB on process ' + str(os.getpid()))            
               