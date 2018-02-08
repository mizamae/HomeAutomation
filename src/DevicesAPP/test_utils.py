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

import webtest

from .constants import DTYPE_DIGITAL,DTYPE_FLOAT,DTYPE_INTEGER,APP_TEMPLATE_NAMESPACE, \
                    FORM_FIRST_RENDER_MSG,FORM_ISVALID_MSG,FORM_ISNOTVALID_MSG,SCAN_DEVICENOFOUND, \
                    SCAN_DEVICEFOUND,TESTS_USER_AGENT,LOCAL_CONNECTION,LINE_PLOT,SPLINE_PLOT,COLUMN_PLOT,AREA_PLOT,\
                    DG_SYNCHRONOUS,DG_ASYNCHRONOUS,\
                    GPIO_DIRECTION_CHOICES,GPIO_OUTPUT,GPIO_INPUT,GPIO_SENSOR,GPIOVALUE_CHOICES,GPIO_HIGH,GPIO_LOW
                    
from .models import Devices,DeviceTypes,Datagrams,DatagramItems,ItemOrdering,MasterGPIOs,MainDeviceVars,\
            MainDeviceVarWeeklySchedules,inlineDaily
from .apps import DevicesAppException
from .forms import DevicesForm,DatagramCustomLabelsForm

import MainAPP.models

# CREATES A BACKUP OF THE REGISTERS DB
from utils.BBDD import backupRegistersDB
backupRegistersDB()

P1=None
P2=None

ApacheHTTPpath=r'C:\xampp\htdocs'

VARWeeklyScheduleDict={'Label':'Weekly schedule test','Var':'','LValue':20,'HValue':25}
MainDeviceVarDict={'Label':'Test Main Var','Value':23,'DataType':DTYPE_DIGITAL,'PlotType':LINE_PLOT,'Units':'H','UserEditable':True}
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
                'Sampletime':10,
                'RTsampletime':10,
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


def editDict(keys,newValues,Dictionary=DeviceDict):
    import copy
    newDict= copy.deepcopy(Dictionary)
    for key,newValue in zip(keys,newValues):
        if not key in newDict:
            raise ValueError('The key ' + key+ ' is not in dictionary DeviceDict')
        newDict[key]=newValue
    return newDict


def startApache():
    global P1
    import subprocess,time
    P1=subprocess.Popen(r'c:\xampp\apache_start.bat')
    time.sleep(2)
 
def stopApache():
    global P2
    import subprocess,time
    P2=subprocess.Popen(r'c:\xampp\apache_stop.bat')
    time.sleep(2)

def setupPowersXML(code,datagramId=0,status=7,p='64,80,0,0',q='64,79,99,0',s='64,80,128,0'):
    import shutil
    file=join(ApacheHTTPpath, 'powers.xml')
    shutil.copy(src=join(ApacheHTTPpath, 'powers_generic.xml'), dst=file)
    
    import fileinput

    with fileinput.FileInput(files=file, inplace=True) as file:
        for line in file:
            print(line.replace('#code#', str(code))
                  .replace('#dId#', str(datagramId))
                  .replace('#status#', str(status))
                  .replace('#p#', str(p))
                  .replace('#q#', str(q))
                  .replace('#s#', str(s))
                  , end='')
         
def resetPowersXML():
    file=join(ApacheHTTPpath, 'powers.xml')
    import os
    try:
        os.remove(path=file)
    except:
        pass