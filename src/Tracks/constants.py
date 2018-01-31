'''
Created on 31 mar. 2017

@author: mzabaleta
'''
import datetime
import logging
import os
from django.core.cache import cache

logger = logging.getLogger("project")

now=datetime.datetime.now()

# CONSTANTS OF THE APP
APPNAME='MasterGPIOAPP'
APP_TEMPLATE_NAMESPACE='MGPIO'
BOOTING_MSG=   '''
                
                
                *****************************************************************************************
                *                                                                                       *
                *                     MASTER GPIO APP BOOTING SEQUENCE INITIATED                        *
                *                                                                                       *
                *****************************************************************************************
                '''
# END

# CONSTANTS OF THE MODELS

# END


