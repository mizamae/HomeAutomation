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

# APPLICATION PATHS
PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
GIT_PATH = os.path.join(PROJECT_PATH,'..','..')
BLOCK_IPS_PATH=os.path.abspath(os.path.join(os.sep,'etc','nginx','blockips.conf'))
NGINX_CONF_PATH=os.path.abspath(os.path.join(os.sep,'etc','nginx','sites-available','HomeAutomation.nginxconf'))
APACHE_HTPASSWD_PATH=os.path.abspath(os.path.join(os.sep,'etc','apache2','.htpasswd'))
LOCALENV_PATH=os.path.join(PROJECT_PATH,'settings','local.env')
WIFI_CONF_PATH=os.path.abspath(os.path.join(os.sep,'etc','hostapd','hostapd.conf'))
INTERFACES_CONF_PATH=os.path.abspath(os.path.join(os.sep,'etc','network','interfaces'))
# APPLICATION DATABASES
DJANGO_DB_PATH = os.path.join(PROJECT_PATH,'..','db.sqlite3')
REGISTERS_DB_PATH = os.path.join(PROJECT_PATH,'..','..', 'Registers_XYEARX_.sqlite3')
# END

MANAGEMENT_TASKS_SCHEDULER_URL='sqlite:///TasksScheduler.sqlite'
AVAR_OVERRIDE_SCHEDULER_URL='sqlite:///OverrideScheduler.sqlite'

AUTOMATION_ACTION_CHOICES=(
        ('a',_('Activate output on Main')),
        ('b',_('Send command to a device')),
        ('c',_('Send an email')),
        ('z',_('None')),
    )

JS_MONTHS_OFFSET=1 # offset to substact to refer months to javascript (zero-based)

SUBSYSTEM_HEATING=0
SUBSYSTEM_GARDEN=1
SUBSYSTEM_ACCESS=2
SUBSYSTEMS_CHOICES=(
                    (SUBSYSTEM_HEATING,_('Heating control')),
                    (SUBSYSTEM_GARDEN,_('Garden control')),
                    (SUBSYSTEM_ACCESS,_('Access control')),
                )

BOOTING_MSG=   '''
                
                
                *****************************************************************************************
                *                                                                                       *
                *                         MAIN APP BOOTING SEQUENCE INITIATED                           *
                *                                                                                       *
                *****************************************************************************************
                '''