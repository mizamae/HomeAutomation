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

PROJECT_PATH = os.path.abspath(os.path.realpath(__file__))
GIT_PATH = os.path.join(PROJECT_PATH,'..','..')

# APPLICATION DATABASES
DJANGO_DB_PATH = os.path.join(PROJECT_PATH,'..')
REGISTERS_DB_PATH = os.path.join(PROJECT_PATH,'..','..', 'Registers_XYEARX_.sqlite3')
# END

MANAGEMENT_TASKS_SCHEDULER_URL='sqlite:///TasksScheduler.sqlite'

BOOTING_MSG=   '''
                
                
                *****************************************************************************************
                *                                                                                       *
                *                         MAIN APP BOOTING SEQUENCE INITIATED                           *
                *                                                                                       *
                *****************************************************************************************
                '''