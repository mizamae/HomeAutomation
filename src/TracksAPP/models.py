# coding: utf-8
from django.utils.translation import ugettext as _

from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save,post_delete,pre_delete

from DevicesAPP.models import Devices
import logging

logger = logging.getLogger("project")

class Beacons(models.Model):
    Identifier = models.CharField(max_length=20,unique=True,error_messages={'unique':_("Invalid Beacon name - This name already exists in the DB.")})
    Latitude = models.FloatField()
    Longitude = models.FloatField()
    WeatherObserver=models.OneToOneField(Devices,on_delete=models.CASCADE,related_name='device2beacons',
                                         null=True,blank=True,limit_choices_to={'DVT__Code': 'OpenWeatherMap'})

    def distance_to(self,other):
        from math import sin, cos, sqrt, atan2, radians
        # approximate radius of earth in km
        R = 6373.0
        lat1 = radians(self.Latitude)
        lon1 = radians(self.Longitude)
        lat2 = radians(other.Latitude)
        lon2 = radians(other.Longitude)
        
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        distance = R * c
        return round(distance,1)
    
    def __str__(self):
        return self.Identifier
