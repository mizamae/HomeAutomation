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
APPNAME='DevicesAPP'
APP_TEMPLATE_NAMESPACE='Devices'
BOOTING_MSG=   '''
                
                
                *****************************************************************************************
                *                                                                                       *
                *                       DEVICES APP BOOTING SEQUENCE INITIATED                          *
                *                                                                                       *
                *****************************************************************************************
                '''
# END

# CONSTANTS OF THE REGISTERS DB
DEVICES_ROOT = os.path.dirname(os.path.realpath(__file__))
REGISTERS_DB_PATH = os.path.join(DEVICES_ROOT,'..','..', 'Registers_XYEARX_.sqlite3')
# END

# CONSTANTS OF THE MODELS
POLLING_SCHEDULER_URL='sqlite:///DevicesScheduler.sqlite'

DEVICES_SUBNET='10.10.10.'      # IP SUBNET FOR THE REMOTE DEVICES
DEVICES_SCAN_IP4BYTE='254'           # LAST BYTE OF IP ADDRESS FOR DEVICES IN SCAN MODE

LOCAL_CONNECTION=0
REMOTE_CONNECTION=1
MEMORY_CONNECTION=3
CONNECTION_CHOICES=(
                    (LOCAL_CONNECTION,'LOCAL'),
                    (REMOTE_CONNECTION,'REMOTE'),
                    (MEMORY_CONNECTION,'MEMORY')
                )

STOPPED_STATE=0
RUNNING_STATE=0
STATE_CHOICES=(
                (STOPPED_STATE,'STOPPED'),
                (RUNNING_STATE,'RUNNING')
            )
# END

# CONSTANTS FOR THE POLLING
DEVICES_CONFIG_FILE='Conf.xml'
IP_OFFSET=1 # establishes the offset for IP addresses and DeviceCode. The IP of the first device will be XXX.XXX.XXX.(IP_OFFSET+1)
JS_MONTHS_OFFSET=1 # offset to substact to refer months to javascript (zero-based)
# END

