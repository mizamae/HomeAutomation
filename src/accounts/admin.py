from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django import forms
from django.utils.functional import curry

import json

from django.utils.translation import ugettext_lazy as _

from Master_GPIOs.models import IOmodel
from RemoteDevices.models import DeviceModel as RemoteDeviceModel
from RemoteDevices.forms import DeviceForm as RemoteDeviceForm

from LocalDevices.models import DeviceModel as LocalDeviceModel
from LocalDevices.forms import DeviceForm as LocalDeviceForm

from Devices.models import DeviceTypeModel,DigitalItemModel,AnalogItemModel,DatagramModel,ItemOrdering,CommandModel,ReportModel,ReportItems
from Devices.forms import DeviceTypeForm as DeviceTypeForm, ItemOrderingForm

from HomeAutomation.models import MainDeviceVarModel,MainDeviceVarWeeklyScheduleModel,inlineDaily,AutomationRuleModel,AutomationVariablesModel
from HomeAutomation.forms import MainDeviceVarForm,inlineDailyForm,AutomationRuleForm

class IOmodelAdmin(admin.ModelAdmin):
    list_display = ('label','pin','direction','value')

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

class DigitalItemModelAdmin(admin.ModelAdmin):
    list_display = ('DBTag','HumanTag')
    pass

class AnalogItemModelAdmin(admin.ModelAdmin):
    list_display = ('DBTag','HumanTag')
    pass

class ItemOrderingInline(admin.TabularInline):
    model = ItemOrdering
    extra = 1 # how many rows to show
    form=ItemOrderingForm
    
class DatagramModelAdmin(admin.ModelAdmin):
    #filter_horizontal = ('AnItems','DgItems')
    list_display = ('DeviceType','Code','Identifier')
    ordering=('DeviceType','Code')
    inlines = (ItemOrderingInline,)
    pass
    
class ReportModelAdmin(admin.ModelAdmin):
    pass

class ReportItemsModelAdmin(admin.ModelAdmin):
    list_display = ('Report','fromDate','toDate')
    ordering=('Report','fromDate')
    pass
    
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
    
class DeviceTypeModelAdmin(admin.ModelAdmin):
    list_display = ('Code','Description','Connection')
    form=DeviceTypeForm
    pass

class CommandModelAdmin(admin.ModelAdmin):
    list_display = ('DeviceType','Identifier','HumanTag')
    pass  

class MainDeviceVarModelAdmin(admin.ModelAdmin):
    def printValue(self,instance):
        return str(instance.Value)+' '+instance.Units
    
    printValue.short_description = _("Current value")
    
    list_display = ('Label','printValue')
    form = MainDeviceVarForm
    pass      

class inlineDailyFormset(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(inlineDailyFormset, self).__init__(*args, **kwargs)
            
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
        formset = super(inlineDailyAdmin, self).get_formset(request, obj, **kwargs)
        formset.__init__ = curry(formset.__init__, initial=initial)
        return formset
    
    #readonly_fields=('Day',)
    
class MainDeviceVarWeeklyScheduleModelAdmin(admin.ModelAdmin):
    #filter_horizontal = ('AnItems','DgItems')
    actions=['setAsActive']
    list_display = ('Label','Active','Var','printValue','printSetpoint')
    ordering=('-Active','Label')
    inlines = (inlineDailyAdmin,)
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
        super(MainDeviceVarWeeklyScheduleModelAdmin, self).save_related(request, form, formsets, change)
        if change:
            from HomeAutomation.models import checkHourlySchedules
            checkHourlySchedules()
    
    def setAsActive(self,request, queryset):
        devices_selected=queryset.count()
        if devices_selected>1:
            self.message_user(request, "Only one schedule can be selected for this action")
        else:
            selected_pk = int(request.POST.getlist(admin.ACTION_CHECKBOX_NAME)[0])
            schedule=MainDeviceVarWeeklyScheduleModel.objects.get(pk=selected_pk)
            schedule.Active=True
            schedule.save()
            return HttpResponseRedirect('/admin/HomeAutomation/maindevicevarweeklyschedulemodel/')
        
    setAsActive.short_description = _("Set as active schedule")
    #extra = 1 # how many rows to show
    #form=ItemOrderingForm

class AutomationRuleModelAdmin(admin.ModelAdmin):
    #filter_horizontal = ('AnItems','DgItems')
    actions=['activate']
    list_display = ('Identifier','Active','Action')
    ordering=('-Active','Identifier')
    form = AutomationRuleForm
    
    def activate(self,request, queryset):
        selected_pk = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)[0]
        rule=AutomationRuleModel.objects.get(pk=selected_pk)
        rule.Active=True
        rule.save()
        return HttpResponseRedirect('/admin/HomeAutomation/automationrulemodel/')
    
    activate.short_description = _("Activate the rule")

class AutomationVariablesModelAdmin(admin.ModelAdmin):
    #filter_horizontal = ('AnItems','DgItems')
    list_display = ('Label','Device', 'Table','Tag','BitPos','Sample')
    ordering=('Device','Table','BitPos')
    def get_actions(self, request):
        #Disable delete
        actions = super(AutomationVariablesModelAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
    
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request):
        return False
                
admin.site.register(IOmodel,IOmodelAdmin)
admin.site.register(RemoteDeviceModel,RemoteDeviceModelAdmin)
admin.site.register(ReportModel,ReportModelAdmin)
admin.site.register(ReportItems,ReportItemsModelAdmin)
admin.site.register(LocalDeviceModel,LocalDeviceModelAdmin)
admin.site.register(DeviceTypeModel,DeviceTypeModelAdmin)

admin.site.register(DigitalItemModel,DigitalItemModelAdmin)
admin.site.register(AnalogItemModel,AnalogItemModelAdmin)
admin.site.register(DatagramModel,DatagramModelAdmin)
admin.site.register(CommandModel,CommandModelAdmin)

admin.site.register(MainDeviceVarModel,MainDeviceVarModelAdmin)
admin.site.register(MainDeviceVarWeeklyScheduleModel,MainDeviceVarWeeklyScheduleModelAdmin)
admin.site.register(AutomationRuleModel,AutomationRuleModelAdmin)
admin.site.register(AutomationVariablesModel,AutomationVariablesModelAdmin)
