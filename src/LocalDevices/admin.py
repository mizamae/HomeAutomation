from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django import forms
from django.utils.functional import curry

import json

from django.utils.translation import ugettext_lazy as _

from LocalDevices.models import DeviceModel as LocalDeviceModel
from LocalDevices.forms import DeviceForm as LocalDeviceForm

    
class LocalDeviceModelAdmin(admin.ModelAdmin):
    list_display = ('DeviceName','Type','DeviceState','Sampletime')
    form=LocalDeviceForm
    actions=['defineCustomLabels']
    
    def defineCustomLabels(self,request, queryset):
        devices_selected=queryset.count()
        if devices_selected>1:
            self.message_user(request, "Only one device can be selected for this action")
        else:
            selected_pk = int(request.POST.getlist(admin.ACTION_CHECKBOX_NAME)[0])
            return HttpResponseRedirect('/admin/LocalDevices/setcustomlabels/local/' + str(selected_pk))
        
    def save_model(self, request, obj, form, change):
        if 'DeviceName' in form.changed_data:
            messages.add_message(request, messages.INFO, 'DeviceName has been changed')
        super(LocalDeviceModelAdmin, self).save_model(request, obj, form, change)

    defineCustomLabels.short_description = _("Define custom labels for the variables")
    

admin.site.register(LocalDeviceModel,LocalDeviceModelAdmin)
