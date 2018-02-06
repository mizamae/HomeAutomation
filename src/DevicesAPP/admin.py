from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django import forms
from django.utils.functional import curry
from django.urls import reverse

import json

from django.utils.translation import ugettext_lazy as _

from MainAPP.admin import SubsystemsInline

from .constants import APP_TEMPLATE_NAMESPACE,GPIO_SENSOR
from DevicesAPP.models import DeviceTypes,DatagramItems,Datagrams,ItemOrdering,DeviceCommands,Devices,Beacons,MasterGPIOs,MainDeviceVars
from DevicesAPP.forms import DeviceTypesForm, ItemOrderingForm,DevicesForm,BeaconsForm,MasterGPIOsForm,MainDeviceVarsForm

class MainDeviceVarsAdmin(admin.ModelAdmin):
    def printValue(self,instance):
        return str(instance.Value)+' '+instance.Units
    
    printValue.short_description = _("Current value")
    
    list_display = ('pk','Label','printValue')
    form = MainDeviceVarsForm
    
    inlines = [
        SubsystemsInline,
    ]      

class MasterGPIOsAdmin(admin.ModelAdmin):
    list_display = ('Pin','Label','Direction','Value')
    form=MasterGPIOsForm
    
    inlines = [
        SubsystemsInline,
    ]
    def save_model(self, request, obj, form, change):
        if not change and obj.Direction!=GPIO_SENSOR: # the object is being created
            obj.store2DB()
        else:
            super().save_model(request, obj, form, change)

class DeviceTypeAdmin(admin.ModelAdmin):
    list_display = ('Code','Description','Connection')
    form=DeviceTypesForm
    pass
    
class DevicesAdmin(admin.ModelAdmin):
    def Connection(self,instance):
        return str(instance.DVT.get_Connection_display())
    
    list_display = ('pk','Name','DVT','Connection','State','Sampletime')
    form=DevicesForm
    actions=['defineCustomLabels']
    
    inlines = [
        SubsystemsInline,
    ]
    
    def defineCustomLabels(self,request, queryset):
        devices_selected=queryset.count()
        if devices_selected>1:
            self.message_user(request, "Only one device can be selected for this action")
        else:
            selected_pk = int(request.POST.getlist(admin.ACTION_CHECKBOX_NAME)[0])
            return HttpResponseRedirect(reverse(APP_TEMPLATE_NAMESPACE+':setCustomLabels',args=[selected_pk]))#'/admin/Devices/setcustomlabels/' + str(selected_pk))
        
    def save_model(self, request, obj, form, change):
        if 'Sampletime' in form.changed_data or 'State' in form.changed_data:
            obj.update_requests()
        super(DevicesAdmin, self).save_model(request, obj, form, change)

    defineCustomLabels.short_description = _("Define custom labels for the variables")
    

class DatagramItemModelAdmin(admin.ModelAdmin):
    list_display = ('pk','Tag','DataType')
    pass

class ItemOrderingInline(admin.TabularInline):
    model = ItemOrdering
    extra = 1 # how many rows to show
    form=ItemOrderingForm
    
class DatagramsAdmin(admin.ModelAdmin):
    #filter_horizontal = ('AnItems','DgItems')
    list_display = ('pk','Type','Code','Identifier')
    ordering=('Type','Code')
    inlines = (ItemOrderingInline,)
    
    def save_related(self, request, form, formsets, change):
        super(DatagramsAdmin, self).save_related(request, form, formsets, change)
        if change:
            DVT=form.cleaned_data['DVT']
            DVs=Devices.objects.filter(Type=DVT)
            for DV in DVs:
                DV.updateCustomLabels()
            

    
class DeviceCommandsAdmin(admin.ModelAdmin):
    list_display = ('DVT','Identifier','HumanTag')
    pass  

class BeaconsAdmin(admin.ModelAdmin):
     list_display = ('Identifier','Latitude','Longitude')
     form=BeaconsForm

admin.site.register(MainDeviceVars,MainDeviceVarsAdmin)
admin.site.register(MasterGPIOs,MasterGPIOsAdmin)
admin.site.register(DeviceTypes,DeviceTypeAdmin)
admin.site.register(Devices,DevicesAdmin)
admin.site.register(DatagramItems,DatagramItemModelAdmin)
admin.site.register(Datagrams,DatagramsAdmin)
admin.site.register(DeviceCommands,DeviceCommandsAdmin)
admin.site.register(Beacons,BeaconsAdmin)