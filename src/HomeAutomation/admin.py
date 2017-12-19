from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django import forms
from django.utils.functional import curry

import json

from django.utils.translation import ugettext_lazy as _



from HomeAutomation.models import MainDeviceVarModel,AdditionalCalculationsModel,MainDeviceVarWeeklyScheduleModel,inlineDaily,AutomationRuleModel,AutomationVariablesModel,RuleItem
from HomeAutomation.forms import MainDeviceVarForm,AdditionalCalculationsForm,inlineDailyForm,AutomationRuleForm,RuleItemForm



class MainDeviceVarModelAdmin(admin.ModelAdmin):
    def printValue(self,instance):
        return str(instance.Value)+' '+instance.Units
    
    printValue.short_description = _("Current value")
    
    list_display = ('Label','printValue','pk')
    form = MainDeviceVarForm
    pass      

class AdditionalCalculationsModelAdmin(admin.ModelAdmin):
    def printCalculation(self,instance):
        return str(instance)
    
    printCalculation.short_description = _("Description")
    
    list_display = ('printCalculation',)
    form = AdditionalCalculationsForm
    
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

class RuleItemInline(admin.TabularInline):
    model = RuleItem
    extra = 0 # how many rows to show
    form=RuleItemForm
    ordering=('order',)

class RuleItemAdmin(admin.ModelAdmin):
    pass


class AutomationRuleModelAdmin(admin.ModelAdmin):
    actions=['activate']
    list_display = ('Identifier','Active','Action','printEvaluation')
    ordering=('-Active','Identifier')
    form = AutomationRuleForm
    
    inlines = (RuleItemInline,)
    
    def printEvaluation(self,instance):
        result=instance.evaluate()
        if result['ERROR']==[]:
            result.pop('ERROR', None)
        return str(result)
    printEvaluation.short_description = _("Current value")
    
    def save_related(self, request, form, formsets, change):
        super(AutomationRuleModelAdmin, self).save_related(request, form, formsets, change)
        #if change:
        AR = AutomationRuleModel.objects.get(Identifier=request.POST['Identifier'])
        if AR.Active:
            AR.execute()
            
    def activate(self,request, queryset):
        selected_pk = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)[0]
        rule=AutomationRuleModel.objects.get(pk=selected_pk)
        rule.Active=True
        rule.save()
        return HttpResponseRedirect('/admin/HomeAutomation/automationrulemodel/')
    
    activate.short_description = _("Activate the rule")
    
    def save(self, *args, **kwargs):                             
        instance = super(AutomationRuleModelAdmin, self).save(*args, **kwargs)   
        if instance.pk:
          for item in instance.RuleItems.all():
            if item not in self.cleaned_data['RuleItems']:            
              # we remove books which have been unselected 
              instance.RuleItems.remove(item)
          for item in self.cleaned_data['RuleItems']:                  
            if item not in instance.RuleItems.all():                   
              # we add newly selected books
              instance.RuleItems.add(item)      
        return instance

class AutomationVariablesModelAdmin(admin.ModelAdmin):
    #filter_horizontal = ('AnItems','DgItems')
    list_display = ('Label','Device', 'Table','Tag','BitPos','Sample')
    ordering=('Device','Table','BitPos')
    def get_actions(self, request):
        #Disable delete
        actions = super(AutomationVariablesModelAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
    
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
                

admin.site.register(MainDeviceVarModel,MainDeviceVarModelAdmin)
admin.site.register(AdditionalCalculationsModel,AdditionalCalculationsModelAdmin)
admin.site.register(MainDeviceVarWeeklyScheduleModel,MainDeviceVarWeeklyScheduleModelAdmin)
admin.site.register(AutomationRuleModel,AutomationRuleModelAdmin)
admin.site.register(AutomationVariablesModel,AutomationVariablesModelAdmin)
admin.site.register(RuleItem,RuleItemAdmin)
