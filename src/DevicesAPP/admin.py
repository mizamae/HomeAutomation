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
from DevicesAPP.models import DeviceTypes,DatagramItems,Datagrams,ItemOrdering,DeviceCommands,Devices,Beacons,\
                            MasterGPIOs,MainDeviceVars,inlineDaily,MainDeviceVarWeeklySchedules
from DevicesAPP.forms import DeviceTypesForm, ItemOrderingForm,DevicesForm,BeaconsForm,MasterGPIOsForm,MainDeviceVarsForm,\
                            inlineDailyForm

class MainDeviceVarsAdmin(admin.ModelAdmin):
    def printValue(self,instance):
        if instance.Units!=None:
            return str(instance.Value)+' '+instance.Units
        else:
            return str(instance.Value)
    
    printValue.short_description = _("Current value")
    
    list_display = ('pk','Label','printValue')
    form = MainDeviceVarsForm
    
    inlines = [
        SubsystemsInline,
    ]
    
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.updateAutomationVars()

class inlineDailyFormset(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
         
class inlineDailyAdmin(admin.TabularInline):
    model = inlineDaily
    max_num=7
    #readonly_fields=('Day',)
    fields=['Day','Hour0','Hour1','Hour2','Hour3','Hour4','Hour5','Hour6','Hour7','Hour8','Hour9','Hour10'
                ,'Hour11','Hour12','Hour13','Hour14','Hour15','Hour16','Hour17','Hour18','Hour19','Hour20','Hour21','Hour22','Hour23']
    min_num=7
    formset = inlineDailyFormset
    form=inlineDailyForm
      
    def get_formset(self, request, obj=None, **kwargs):
        initial = []
        if request.method == "GET":
            initial=[
                        {'Day': 0},  
                        {'Day': 1}, 
                        {'Day': 2},
                        {'Day': 3},
                        {'Day': 4},
                        {'Day': 5},
                        {'Day': 6}]
        formset = super().get_formset(request, obj, **kwargs)
        formset.__init__ = curry(formset.__init__, initial=initial)
        return formset
    
class MainDeviceVarWeeklySchedulesAdmin(admin.ModelAdmin):
    actions=['setAsActive']
    list_display = ('Label','Active','Var','printValue','printSetpoint')
    ordering=('-Active','Label')
    inlines = (SubsystemsInline,inlineDailyAdmin,)
    exclude = ('Days',)
      
    def printValue(self,instance):
        return str(instance.Var.Value)+' '+instance.Var.Units
    printValue.short_description = _("Current value")
      
    def printSetpoint(self,instance):
        import datetime
        timestamp=datetime.datetime.now()
        weekDay=timestamp.weekday()
        hour=timestamp.hour
        dailySchedules=instance.inlinedaily_set.all()
        for daily in dailySchedules:
            if daily.Day==weekDay:
                Setpoint=getattr(daily,'Hour'+str(hour))
                if Setpoint==0:
                    return str(instance.LValue)+' '+instance.Var.Units
                else:
                    return str(instance.HValue)+' '+instance.Var.Units
    printSetpoint.short_description = _("Current setpoint")
      
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if change:
            form.instance.checkThis()
    
    def save_model(self, request, obj, form, change):
        if not change: # the object is being created
            obj.store2DB()
        else:
            super().save_model(request, obj, form, change)
            
    def setAsActive(self,request, queryset):
        devices_selected=queryset.count()
        if devices_selected>1:
            self.message_user(request, "Only one schedule can be selected for this action")
        else:
            selected_pk = int(request.POST.getlist(admin.ACTION_CHECKBOX_NAME)[0])
            schedule=MainDeviceVarWeeklySchedules.objects.get(pk=selected_pk)
            schedule.setActive()
            return HttpResponseRedirect('/admin/DevicesAPP/maindevicevarweeklyschedules/')
          
    setAsActive.short_description = _("Set as active schedule")
    #extra = 1 # how many rows to show
    #form=ItemOrderingForm

class MasterGPIOsAdmin(admin.ModelAdmin):
    list_display = ('Pin','Label','Direction','Value')
    form=MasterGPIOsForm
    
    inlines = [
        SubsystemsInline,
    ]

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
        if not change: # the object is being created
            obj.store2DB()
        else:
            if 'Sampletime' in form.changed_data or 'State' in form.changed_data:
                obj.updateAutomationVars()
                obj.updateRequests()
            super().save_model(request, obj, form, change)

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
            DVs=Devices.objects.filter(DVT=DVT)
            for DV in DVs:
                DV.setCustomLabels()
            

    
class DeviceCommandsAdmin(admin.ModelAdmin):
    list_display = ('DVT','Identifier','HumanTag')
    pass  

class BeaconsAdmin(admin.ModelAdmin):
     list_display = ('Identifier','Latitude','Longitude')
     form=BeaconsForm

admin.site.register(MainDeviceVars,MainDeviceVarsAdmin)
admin.site.register(MainDeviceVarWeeklySchedules,MainDeviceVarWeeklySchedulesAdmin)
admin.site.register(MasterGPIOs,MasterGPIOsAdmin)
admin.site.register(DeviceTypes,DeviceTypeAdmin)
admin.site.register(Devices,DevicesAdmin)
admin.site.register(DatagramItems,DatagramItemModelAdmin)
admin.site.register(Datagrams,DatagramsAdmin)
admin.site.register(DeviceCommands,DeviceCommandsAdmin)
admin.site.register(Beacons,BeaconsAdmin)