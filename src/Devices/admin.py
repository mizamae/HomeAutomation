from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django import forms
from django.utils.functional import curry

import json

from django.utils.translation import ugettext_lazy as _

from Devices.models import DeviceTypeModel,DigitalItemModel,AnalogItemModel,DatagramModel,ItemOrdering,CommandModel,ReportModel,ReportItems
from Devices.forms import DeviceTypeForm as DeviceTypeForm, ItemOrderingForm

class DeviceTypeModelAdmin(admin.ModelAdmin):
    list_display = ('Code','Description','Connection')
    form=DeviceTypeForm
    pass

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
    
class DeviceTypeModelAdmin(admin.ModelAdmin):
    list_display = ('Code','Description','Connection')
    form=DeviceTypeForm
    pass

class CommandModelAdmin(admin.ModelAdmin):
    list_display = ('DeviceType','Identifier','HumanTag')
    pass  

admin.site.register(DeviceTypeModel,DeviceTypeModelAdmin)
admin.site.register(DigitalItemModel,DigitalItemModelAdmin)
admin.site.register(AnalogItemModel,AnalogItemModelAdmin)
admin.site.register(DatagramModel,DatagramModelAdmin)
admin.site.register(CommandModel,CommandModelAdmin)

