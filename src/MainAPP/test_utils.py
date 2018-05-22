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

from .constants import SUBSYSTEM_HEATING
                    
from .models import Subsystems,AutomationVariables,RuleItems,AutomationRules,AdditionalCalculations,AutomationVarWeeklySchedules,inlineDaily

from DevicesAPP.models import MasterGPIOs,MainDeviceVars

from DevicesAPP.constants import GPIO_OUTPUT,GPIO_INPUT,GPIO_HIGH,GPIO_LOW
                    
#from .forms import AdditionalCalculationsForm,RuleItemForm,AutomationRuleForm

from .signals import SignalSetGPIO

from utils.test_utils import *

VARWeeklyScheduleDict={'Label':'Weekly schedule test','Var':'','LValue':20,'HValue':25}
AdditionalCalculationsDict={'SourceVar':None,'SinkVar':None,'Periodicity':2,'Calculation':0}
AutomationVariablesDict={'Label':'Test Automation Var1','Tag':'1','Device':'MainVars','Table':'MainVariables',
                         'BitPos':None,'Sample':1,'Units':'kW'}
RuleItemsDict={'Rule':'','Order':1,'PreVar1':'','Var1':'','Operator12':'>','PreVar2':'','Var2':'','Var2Hyst':0.2,
               'IsConstant':False,'Constant':20,'Operator3':'|'}
AutomationRulesDict={'Identifier':'Test Rule','Active':False,'OnError':0,'PreviousRule':None,'OperatorPrev':'',
                     'Action':'{"IOValue": "0", "ActionType": "a", "Device": null, "Order": null, "IO": 18}'}

