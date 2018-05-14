from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django import forms
from django.utils.functional import curry

import json

from django.utils.translation import ugettext_lazy as _

from TracksAPP.models import Beacons
from TracksAPP.forms import BeaconForm
    
class BeaconModelAdmin(admin.ModelAdmin):
     list_display = ('Identifier','Latitude','Longitude')
     form=BeaconForm

admin.site.register(Beacons,BeaconModelAdmin)

# GOOGLEMAPS API KEY= AIzaSyARa_5fk7pCUNLM9Ce_czcokqdVbn5PLyQ