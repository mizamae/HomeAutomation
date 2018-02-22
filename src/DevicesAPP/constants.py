'''
Created on 31 mar. 2017

@author: mzabaleta
'''
import datetime

import os
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _

import logging
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
DEVICESAPP_ROOT = os.path.dirname(os.path.realpath(__file__))
DECIMAL_POSITIONS=3
# END

# CONSTANTS OF THE MODELS
GPIO_OUTPUT=0
GPIO_INPUT=1
GPIO_SENSOR=2
GPIO_DIRECTION_CHOICES=(
                        (GPIO_OUTPUT,_('Output')),
                        (GPIO_INPUT,_('Input')),
                        (GPIO_SENSOR,_('Sensor')),
                    )
GPIO_LOW=0
GPIO_HIGH=1
GPIOVALUE_CHOICES=(
                (GPIO_LOW,_('LOW')),
                (GPIO_HIGH,_('HIGH')),
            )
GPIO_IN_DBTABLE='inputs'
GPIO_OUT_DBTABLE='outputs'

POLLING_SCHEDULER_URL='sqlite:///'+DEVICESAPP_ROOT+'/DevicesScheduler.sqlite'

LOCAL_CONNECTION=0
REMOTE_TCP_CONNECTION=1
MEMORY_CONNECTION=2
CONNECTION_CHOICES=(
                    (LOCAL_CONNECTION,_('LOCAL')),
                    (REMOTE_TCP_CONNECTION,_('REMOTE OVER TCP')),
                    (MEMORY_CONNECTION,_('MEMORY'))
                )

STOPPED_STATE=0
RUNNING_STATE=1
STATE_CHOICES=(
                (STOPPED_STATE,'STOPPED'),
                (RUNNING_STATE,'RUNNING')
            )

DG_SYNCHRONOUS=0
DG_ASYNCHRONOUS=1
DATAGRAMTYPE_CHOICES=(
        (DG_SYNCHRONOUS,'Synchronous'),
        (DG_ASYNCHRONOUS,'Asynchronous')
    )

DTYPE_INTEGER='integer'
DTYPE_FLOAT='float'
DTYPE_DIGITAL='digital'
DATATYPE_CHOICES=(
        (DTYPE_INTEGER,_('Analog Integer')),
        (DTYPE_FLOAT,_('Analog Float')),
        (DTYPE_DIGITAL,_('Digital')),
        )

LINE_PLOT='line'
SPLINE_PLOT='spline'
COLUMN_PLOT='column'
AREA_PLOT='area'

PLOTTYPE_CHOICES=(
        (LINE_PLOT,_('Hard Line')),
        (SPLINE_PLOT,_('Smoothed Line')),
        (COLUMN_PLOT,_('Bars')),
        (AREA_PLOT,_('Area')),
    )
    
# END

# CONSTANTS FOR THE POLLING
DEVICES_PROTOCOL='http://'
DEVICES_SUBNET='10.10.10.'      # IP SUBNET FOR THE REMOTE DEVICES
DEVICES_SCAN_IP4BYTE='254'           # LAST BYTE OF IP ADDRESS FOR DEVICES IN SCAN MODE
DEVICES_CONFIG_FILE='Conf.xml'
IP_OFFSET=1 # establishes the offset for IP addresses and DeviceCode. The IP of the first device will be XXX.XXX.XXX.(IP_OFFSET+1)
JS_MONTHS_OFFSET=1 # offset to substact to refer months to javascript (zero-based)
# END

# CONSTANTS FOR THE TESTS
FORM_FIRST_RENDER_MSG='form is first rendered'
FORM_ISVALID_MSG='form is valid'
FORM_ISNOTVALID_MSG='form is not valid'
SCAN_DEVICEFOUND='Found a Device'
SCAN_DEVICENOFOUND='No device was found'
TESTS_USER_AGENT='stupid-test-agent'