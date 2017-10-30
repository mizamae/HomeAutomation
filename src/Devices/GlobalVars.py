'''
Created on 31 mar. 2017

@author: mzabaleta
'''
import datetime
import logging
import os
from django.core.cache import cache

logger = logging.getLogger("project")

daysmonths_offset=1 # offset to substact to refer months to javascript (zero-based)

now=datetime.datetime.now()

DEVICES_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_PATH = os.path.abspath(os.path.dirname(__name__))
DEVICES_DB_PATH = os.path.join(DEVICES_ROOT,'..','..', 'Devices.sqlite3')
REGISTERS_DB_PATH = os.path.join(DEVICES_ROOT,'..','..', 'Registers_XYEARX_.sqlite3')
XML_CONFFILE_PATH=os.path.join(DEVICES_ROOT,'configuration.xml')

singletaskingProcess=cache.get('single_tasking')
if singletaskingProcess!=None:
    logger.info('DEVICES_ROOT: ' + DEVICES_ROOT ) 
    logger.info('PROJECT_PATH: ' + PROJECT_PATH )
    logger.info('DEVICES_DB_PATH: ' + DEVICES_DB_PATH )
    logger.info('REGISTERS_DB_PATH: ' + REGISTERS_DB_PATH )
    logger.info('XML_CONF_PATH: ' + XML_CONFFILE_PATH )

# Request body to receive the configuration from the slaves
DEVICES_CONFIG_FILE='Conf.xml'

IP_OFFSET=1 # establishes the offset for IP addresses and DeviceCode. The IP of the first device will be XXX.XXX.XXX.(IP_OFFSET+1)

BOOTING_MSG=   '''
                
                
                *****************************************************************************************
                *                                                                                       *
                *                             BOOTING SEQUENCE INITIATED                                *
                *                                                                                       *
                *****************************************************************************************
                '''