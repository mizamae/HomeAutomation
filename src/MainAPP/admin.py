from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
from django.utils.translation import ugettext_lazy as _

from .models import Subsystems,AutomationVariables,RuleItems,AutomationRules,AdditionalCalculations,Thermostats
from .forms import RuleItemForm,AutomationRuleForm,AdditionalCalculationsForm

class SubsystemsInline(GenericStackedInline):
    extra = 1
    model = Subsystems

class AdditionalCalculationsModelAdmin(admin.ModelAdmin):
    def printCalculation(self,instance):
        return str(instance)
     
    printCalculation.short_description = _("Description")
     
    list_display = ('printCalculation',)
    form = AdditionalCalculationsForm
    
    def save_model(self, request, obj, form, change):
        if not change: # the object is being created
            obj.store2DB()
        else:
            super().save_model(request, obj, form, change)
            
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
admin.site.register(AutomationRules,AutomationRuleModelAdmin)
admin.site.register(Thermostats,ThermostatAdmin)
admin.site.register(AutomationVariables,AutomationVariablesModelAdmin)
