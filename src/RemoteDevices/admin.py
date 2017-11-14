from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django import forms
from django.utils.functional import curry

import json

from django.utils.translation import ugettext_lazy as _

from RemoteDevices.models import DeviceModel as RemoteDeviceModel
from RemoteDevices.forms import DeviceForm as RemoteDeviceForm


from Devices.models import DeviceTypeModel,DigitalItemModel,AnalogItemModel,DatagramModel,ItemOrdering,CommandModel,ReportModel,ReportItems
from Devices.forms import DeviceTypeForm as DeviceTypeForm, ItemOrderingForm

from HomeAutomation.models import MainDeviceVarModel,MainDeviceVarWeeklyScheduleModel,inlineDaily,AutomationRuleModel,AutomationVariablesModel
from HomeAutomation.forms import MainDeviceVarForm,inlineDailyForm,AutomationRuleForm


class RemoteDeviceModelAdmin(admin.ModelAdmin):
    actions=['defineCustomLabels']
    list_display = ('DeviceName','DeviceIP','DeviceState','Sampletime')
    form=RemoteDeviceForm
    
    def defineCustomLabels(self,request, queryset):
        devices_selected=queryset.count()
        if devices_selected>1:
            self.message_user(request, "Only one device can be selected for this action")
        else:
            selected_pk = int(request.POST.getlist(admin.ACTION_CHECKBOX_NAME)[0])
            return HttpResponseRedirect('/admin/RemoteDevices/setcustomlabels/remote/' + str(selected_pk))
        
    defineCustomLabels.short_description = _("Define custom labels for the variables")


                

admin.site.register(RemoteDeviceModel,RemoteDeviceModelAdmin)
