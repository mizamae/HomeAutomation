from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect

from django.utils.translation import ugettext_lazy as _

from Master_GPIOs.models import IOmodel
from RemoteDevices.models import DeviceModel as RemoteDeviceModel
from RemoteDevices.forms import DeviceForm as RemoteDeviceForm

from LocalDevices.models import DeviceModel as LocalDeviceModel
from LocalDevices.forms import DeviceForm as LocalDeviceForm

from Devices.models import DeviceTypeModel,DigitalItemModel,AnalogItemModel,DatagramModel,ItemOrdering,CommandModel,ReportModel,ReportItems
from Devices.forms import DeviceTypeForm as DeviceTypeForm, ItemOrderingForm

from HomeAutomation.models import MainDeviceVarModel
from HomeAutomation.forms import MainDeviceVarForm

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
            return HttpResponseRedirect('/admin/RemoteDevices/devicemodel_setcustomlabels/remote/' + str(selected_pk))
        
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
            return HttpResponseRedirect('/admin/LocalDevices/devicemodel_setcustomlabels/local/' + str(selected_pk))
        
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
    
    printValue.short_description = _("Value")
    
    list_display = ('Label','printValue')
    form = MainDeviceVarForm
    pass      
    
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
