from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django import forms
from django.utils.functional import curry

import json

from django.utils.translation import ugettext_lazy as _

from Master_GPIOs.models import IOmodel


class IOmodelAdmin(admin.ModelAdmin):
    list_display = ('label','pin','direction','value')


                
admin.site.register(IOmodel,IOmodelAdmin)
