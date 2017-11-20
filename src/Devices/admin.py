from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django import forms
from django.utils.functional import curry

import json

from django.utils.translation import ugettext_lazy as _

from Devices.models import DeviceTypeModel,DatagramItemModel,DatagramModel,ItemOrdering,CommandModel,ReportModel,ReportItems,DeviceModel
from Devices.forms import DeviceTypeForm as DeviceTypeForm, ItemOrderingForm,DeviceForm

class DeviceModelAdmin(admin.ModelAdmin):
    def Connection(self,instance):
        return str(instance.Type.Connection)
    
    list_display = ('DeviceName','Type','Connection','DeviceState','Sampletime')
    form=DeviceForm
    actions=['defineCustomLabels']
    
    
    
    def defineCustomLabels(self,request, queryset):
        devices_selected=queryset.count()
        if devices_selected>1:
            self.message_user(request, "Only one device can be selected for this action")
        else:
            selected_pk = int(request.POST.getlist(admin.ACTION_CHECKBOX_NAME)[0])
            return HttpResponseRedirect('/admin/Devices/setcustomlabels/' + str(selected_pk))
        
    def save_model(self, request, obj, form, change):
        if 'DeviceName' in form.changed_data:
            messages.add_message(request, messages.INFO, 'DeviceName has been changed')
        super(DeviceModelAdmin, self).save_model(request, obj, form, change)

    defineCustomLabels.short_description = _("Define custom labels for the variables")
    

admin.site.register(DeviceModel,DeviceModelAdmin)

class DeviceTypeModelAdmin(admin.ModelAdmin):
    list_display = ('Code','Description','Connection')
    form=DeviceTypeForm
    pass


class DatagramItemModelAdmin(admin.ModelAdmin):
    list_display = ('HumanTag','DataType')
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
    
    def save_related(self, request, form, formsets, change):
        super(DatagramModelAdmin, self).save_related(request, form, formsets, change)
        if change:
            DVT=form.cleaned_data['DeviceType']
            DVs=DeviceModel.objects.filter(Type=DVT)
            for DV in DVs:
                DV.updateCustomLabels()
            
class ReportModelAdmin(admin.ModelAdmin):
    pass

class ReportItemsModelAdmin(admin.ModelAdmin):
    list_display = ('Report','fromDate','toDate')
    ordering=('Report','fromDate')
    pass
    
class DeviceTypeModelAdmin(admin.ModelAdmin):
    list_display = ('Code','Description','Connection')
    form=DeviceTypeForm
    pass

class CommandModelAdmin(admin.ModelAdmin):
    list_display = ('DeviceType','Identifier','HumanTag')
    pass  

admin.site.register(DeviceTypeModel,DeviceTypeModelAdmin)
admin.site.register(DatagramItemModel,DatagramItemModelAdmin)
admin.site.register(DatagramModel,DatagramModelAdmin)
admin.site.register(CommandModel,CommandModelAdmin)

