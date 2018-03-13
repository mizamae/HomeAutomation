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
import json
                    
from .models import Reports


from .constants import DAILY_PERIODICITY,NO_AGGREGATION

from utils.test_utils import *

jsonContent=[{"report_title":"Prueba","Periodicity":"2","DataAggregation":"1"},[{"chart_title":"Grafico 1"},{"device":"MainGPIOs","table":"outputs","name":"25","bitPos":"0","label":"No se necesita calefaccion","extrapolate":0,"type":"digital","plottype":"line"},],[{"chart_title":"Grafico 2"},{"device":"MainVars","table":"MainVariables","name":"3","bitPos":None,"label":"Temperatura deseada en salon","extrapolate":"keepPrevious","type":"analog","plottype":"spline"},{"device":"MainVars","table":"MainVariables","name":"4","bitPos":None,"label":"Temperatura deseada en dormitorio","extrapolate":"keepPrevious","type":"analog","plottype":"spline"}]]
ReportsDict={'Title':'Test title','Periodicity':DAILY_PERIODICITY,'DataAggregation':NO_AGGREGATION,'ContentJSON':json.dumps(jsonContent)}


