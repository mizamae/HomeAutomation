'''
Created on 31 mar. 2017

@author: mzabaleta
'''
import datetime
import logging
import os
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger("project")

now=datetime.datetime.now()

PROJECT_PATH = os.path.abspath(os.path.realpath(__file__))
GIT_PATH = os.path.join(PROJECT_PATH,'..','..')

# APPLICATION DATABASES
DJANGO_DB_PATH = os.path.join(PROJECT_PATH,'..')
REGISTERS_DB_PATH = os.path.join(PROJECT_PATH,'..','..', 'Registers_XYEARX_.sqlite3')
# END

MANAGEMENT_TASKS_SCHEDULER_URL='sqlite:///TasksScheduler.sqlite'

AUTOMATION_ACTION_CHOICES=(
        ('a',_('Activate output on Main')),
        ('b',_('Send command to a device')),
        ('c',_('Send an email')),
        ('z',_('None')),
    )

SUBSYSTEM_HEATING=0
SUBSYSTEM_GARDEN=1
SUBSYSTEM_ALARM=2
SUBSYSTEMS_CHOICES=(
                    (SUBSYSTEM_HEATING,_('Heating/Cooling')),
                    (SUBSYSTEM_GARDEN,_('Garden')),
                    (SUBSYSTEM_ALARM,_('Alarm')),
                )

BOOTING_MSG=   '''
                
                
                *****************************************************************************************
                *                                                                                       *
                *                         MAIN APP BOOTING SEQUENCE INITIATED                           *
                *                                                                                       *
                *****************************************************************************************
                '''