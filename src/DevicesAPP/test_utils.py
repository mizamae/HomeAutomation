import datetime
from os.path import dirname, join, exists

from django.test import tag
from django.utils import timezone
from django.test import TestCase,Client
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group,Permission
from tzlocal import get_localzone

import time
import webtest

from .constants import DTYPE_DIGITAL,DTYPE_FLOAT,DTYPE_INTEGER,APP_TEMPLATE_NAMESPACE, \
                    FORM_FIRST_RENDER_MSG,FORM_ISVALID_MSG,FORM_ISNOTVALID_MSG,SCAN_DEVICENOFOUND, \
                    SCAN_DEVICEFOUND,TESTS_USER_AGENT,LOCAL_CONNECTION,LINE_PLOT,SPLINE_PLOT,COLUMN_PLOT,AREA_PLOT,\
                    DG_SYNCHRONOUS,DG_ASYNCHRONOUS,\
                    GPIO_DIRECTION_CHOICES,GPIO_OUTPUT,GPIO_INPUT,GPIO_SENSOR,GPIOVALUE_CHOICES,GPIO_HIGH,GPIO_LOW
                    
from .models import Devices,DeviceTypes,Datagrams,DatagramItems,ItemOrdering,MasterGPIOs,MainDeviceVars
from .apps import DevicesAppException
from .forms import DevicesForm,DatagramCustomLabelsForm,MainDeviceVarsForm,MasterGPIOsForm

import MainAPP.models
from .signals import SignalVariableValueUpdated

from utils.test_utils import *

# CREATES A BACKUP OF THE REGISTERS DB
from utils.BBDD import backupRegistersDB
backupRegistersDB()

P1=None
P2=None


MainDeviceVarDict={'Label':'Test Main Var','Value':23,'DataType':DTYPE_INTEGER,'PlotType':LINE_PLOT,'Units':'H','UserEditable':True}
MasterGPIODict={'Pin':17,'Label':'Test Output 1','Direction':GPIO_OUTPUT,'Value':GPIO_HIGH}
DatagramItemDict={'Tag':'Digital Item 1','DataType':DTYPE_DIGITAL,'PlotType':SPLINE_PLOT,'Units':''}
ItemOrderingDict={'DG':'','ITM':'','Order':0}
DatagramDict={'Identifier':'Datagram','Code':0,'Type':DG_SYNCHRONOUS,'DVT':0}

DeviceDict={
                'Name' : 'Test Device 2',
                'IO' : None,
                'Code' : 2,
                'IP' : '127.0.0.1',
                'DVT' : 0,
                'State': 0,
                'Sampletime':60,
                'RTsampletime':60,
                'LastUpdated': None,
                'NextUpdate': None,
                'Connected' : False,  
                'CustomLabels' : '',
                'Error':'',
            }

DevicetypeDict={
                'Code' : 'TestType',
                'Description' : 'Test Description',
                'MinSampletime':60,
                'Connection' : LOCAL_CONNECTION,
            }


