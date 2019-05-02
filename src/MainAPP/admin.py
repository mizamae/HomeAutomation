from django import forms
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import curry
from django.http import HttpResponseRedirect

from .models import Subsystems,AutomationVariables,RuleItems,AutomationRules,AdditionalCalculations,Thermostats,inlineDaily,AutomationVarWeeklySchedules
from .forms import RuleItemForm,AutomationRuleForm,AdditionalCalculationsForm,inlineDailyForm

class SubsystemsInline(GenericStackedInline):
    extra = 1
    model = Subsystems

class AdditionalCalculationsModelAdmin(admin.ModelAdmin):
    actions=['initializeDB',]
    def initializeDB(self,request, queryset):
        ACALCs_selected=queryset.count()
        if ACALCs_selected>1:
            self.message_user(request, "Only one calculation can be selected for this action")
        else:
            selected_pk = int(request.POST.getlist(admin.ACTION_CHECKBOX_NAME)[0])           
            ACALC=AdditionalCalculations.objects.get(pk=selected_pk)
            ACALC.initializeDB()
            return HttpResponseRedirect('/admin/MainAPP/additionalcalculations/')
          
    initializeDB.short_description = _("Initializes the DB from 1st January")
    
    def printCalculation(self,instance):
        return str(instance)
     
    printCalculation.short_description = _("Description")
    
    def printPeriodicity(self,instance):
        if instance.Delay!=0:
            return instance.get_Periodicity_display() + ' - Delay ' + str(instance.Delay)+' h'
        else:
            return instance.get_Periodicity_display()
     
    printPeriodicity.short_description = _("Periodicity")
    
    list_display = ('printCalculation','printPeriodicity')
    form = AdditionalCalculationsForm
    
    def save_model(self, request, obj, form, change):
        if not change: # the object is being created
            obj.store2DB()
        else:
            super().save_model(request, obj, form, change)

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
    
class AutomationVarWeeklySchedulesAdmin(admin.ModelAdmin):
    actions=['setAsActive']
    list_display = ('Label','Active','Var','printValue','printSetpoint')
    ordering=('-Active','Label')
    inlines = (SubsystemsInline,inlineDailyAdmin,)
    exclude = ('Days',)
      
    def printValue(self,instance):
        return str(instance.Var.getLatestValue())+' '+instance.Var.Units
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
            schedule=AutomationVarWeeklySchedules.objects.get(pk=selected_pk)
            schedule.setActive()
            return HttpResponseRedirect('/admin/MainAPP/automationvarweeklyschedules/')
          
    setAsActive.short_description = _("Set as active schedule")
    #extra = 1 # how many rows to show
    #form=ItemOrderingForm
                
class ThermostatAdmin(admin.ModelAdmin):
    pass

class RuleItemInline(admin.TabularInline):
    model = RuleItems
    extra = 0 # how many rows to show
    form=RuleItemForm
    ordering=('Order',)
 
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
        AR = AutomationRules.objects.get(Identifier=request.POST['Identifier'])
        if AR.Active:
            AR.execute()
             
    def activate(self,request, queryset):
        selected_pk = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)[0]
        rule=AutomationRules.objects.get(pk=selected_pk)
        rule.Active=True
        rule.save()
        return HttpResponseRedirect('/admin/MainAPP/automationrulemodel/')
     
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
    
    inlines = [
        SubsystemsInline,
    ]

admin.site.register(AdditionalCalculations,AdditionalCalculationsModelAdmin)
admin.site.register(AutomationVarWeeklySchedules,AutomationVarWeeklySchedulesAdmin)
admin.site.register(AutomationRules,AutomationRuleModelAdmin)
admin.site.register(Thermostats,ThermostatAdmin)
admin.site.register(AutomationVariables,AutomationVariablesModelAdmin)
