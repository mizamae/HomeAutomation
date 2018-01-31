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

# CONSTANTS OF THE APP
APPNAME='ReportingAPP'
APP_TEMPLATE_NAMESPACE='Reports'
BOOTING_MSG=   '''
                
                
                *****************************************************************************************
                *                                                                                       *
                *                      REPORTING APP BOOTING SEQUENCE INITIATED                         *
                *                                                                                       *
                *****************************************************************************************
                '''
# END

# CONSTANTS OF THE REGISTERS DB
DEVICESAPP_ROOT = os.path.dirname(os.path.realpath(__file__))
# END

# CONSTANTS OF THE MODELS
DAILY_PERIODICITY=2
WEEKLY_PERIODICITY=3
MONTHLY_PERIODICITY=4
PERIODICITY_CHOICES=(
        (DAILY_PERIODICITY,_('Every day')),
        (WEEKLY_PERIODICITY,_('Every week')),
        (MONTHLY_PERIODICITY,_('Every month'))
    )

NO_AGGREGATION=0
HOURLY_AGGREGATION=1
DAILY_AGGREGATION=2
MONTHLY_AGGREGATION=4

AGGREGATION_CHOICES=(
        (NO_AGGREGATION,_('No aggregation')),
        (HOURLY_AGGREGATION,_('Hourly')),
        (DAILY_AGGREGATION,_('Daily')),
        (MONTHLY_AGGREGATION,_('Monthly'))
    )
    
# END


