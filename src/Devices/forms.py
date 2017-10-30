# coding: utf-8
import datetime

from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.views import generic
from django.forms import ModelForm

import Devices.BBDD
import Devices.GlobalVars
import LocalDevices.models
import RemoteDevices.models
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field

import logging
logger = logging.getLogger("project")
                               
class DeviceTypeForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(DeviceTypeForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-sm-4'
        self.helper.field_class = 'col-sm-6'
#         self.helper.form_id = 'id-DeviceForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        
        self.fields['Connection'].label = _("Set the connection of the device")
        self.fields['Code'].label = _("Enter the type of the device")
        self.fields['Description'].label = _("Enter the description of the device")
        self.fields['MinSampletime'].label = _("Select the minimum sample time for the device [s]")
        self.fields['Picture'].label = _("Upload an image for the DeviceType")
        
        self.helper.layout = Layout(
            Field('Connection', css_class='input-sm'),
            Field('Code', css_class='input-sm'),
            Field('Description', css_class='input-sm'),
            Field('MinSampletime', css_class='input-sm'),
            Field('Picture'),
            Submit('submit', _('Submit'),css_class='btn-primary'),
            )
        
    class Meta:
        model = Devices.models.DeviceTypeModel
        fields=['Connection','Code','Description','MinSampletime','Picture']

class DatagramCustomLabelsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(DeviceTypeForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-sm-4'
        self.helper.field_class = 'col-sm-6'
#         self.helper.form_id = 'id-DeviceForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        
        datagramlayout=[]
        
        try:
            fields = kwargs.pop('fields')
            super(DatagramCustomLabelsForm, self).__init__(*args, **kwargs)

            for i, field in enumerate(fields):
                self.fields['variable_%s' % i] = forms.CharField(label=field,required=False)
                layout.append(Field('variable_%s' % i, css_class='input-sm'))
            
            layout.append(Submit('submit', _('Submit'),css_class='btn-primary'))
            self.helper.layout = Layout(layout)
        except:
            pass
    
    def get_variablesLabels(self):
        for name, value in self.cleaned_data.items():
            if name.startswith('variable_'):
                yield (self.fields[name].label, value)
                
class ReportForm(ModelForm):  
    
    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-sm-4'
        self.helper.field_class = 'col-sm-6'
#         self.helper.form_id = 'id-DeviceForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        
        self.fields['ReportTitle'].label = _('Title of the report')
        self.fields['Periodicity'].label = _('Setup the periodicity')
        self.fields['DataAggregation'].label = _('Setup the aggregation of the data')
        
        self.helper.layout = Layout(
            Field('ReportTitle', css_class='input-sm'),
            Field('Periodicity', css_class='input-sm'),
            Field('DataAggregation', css_class='input-sm'),
            )
    
    # def clean_Periodicity(self):
        # data = self.cleaned_data['Periodicity']
        # return data
    
    # def clean_DataAggregation(self):
        # data = self.cleaned_data['DataAggregation']
        # return data
        
    def clean(self):
        cleaned_data=super().clean() # to use the validation of the fields from the model
        #logger.info(str(cleaned_data))
        Periodicity = cleaned_data['Periodicity']
        DataAggregation = cleaned_data['DataAggregation']
        if DataAggregation>Periodicity:
           raise ValidationError(_('Incompatibility - The aggregation cannot be bigger than the periodicity.'))
        return cleaned_data
        
    class Meta:
        model = Devices.models.ReportModel
        fields=['ReportTitle','Periodicity','DataAggregation']
 
class ItemOrderingForm(ModelForm):  
    
    def clean(self):
        cleaned_data=super().clean() # to use the validation of the fields from the model
        AnItem = cleaned_data['AnItem']
        DgItem = cleaned_data['DgItem']
        if AnItem!=None and DgItem!=None:
           raise ValidationError(_('You cannot select two items for the same position!!'))
        return cleaned_data
    
    class Meta:
        model = Devices.models.ItemOrdering
        fields=['order','DgItem','AnItem']
        
class DeviceGraphs(forms.Form):
    DeviceName = forms.ChoiceField(label=_('Select the device'))
    fromDate=forms.DateTimeField(label=_('From'),widget=forms.widgets.DateTimeInput(attrs={'id': 'datetimepicker11'}))
    toDate=forms.DateTimeField(label=_('To'),widget=forms.widgets.DateTimeInput(attrs={'id': 'datetimepicker12'}))
    
    def __init__(self, *args, **kwargs):
        super(DeviceGraphs, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        #self.helper.form_id = 'id-DeviceGraphs'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        self.helper.label_class = 'col-sm-4'
        self.helper.field_class = 'col-sm-6'
        
        DVs=RemoteDevices.models.DeviceModel.objects.all()
        device_list=[(1,_('Main Unit'))]
        i=2
        try:
            for device in DVs:
                device_list.append((i,device.DeviceName))
                i+=1
        except: 
            pass   
        DVs=LocalDevices.models.DeviceModel.objects.all()
        try:
            for device in DVs:
                device_list.append((i,device.DeviceName))
                i+=1
        except: 
            pass   
            
        self.fields['DeviceName'].choices=device_list
        now = datetime.datetime.now()
        initfrom=datetime.datetime(now.year,now.month,now.day,0,0,1)
        self.fields['fromDate'].initial=initfrom
        self.fields['toDate'].initial=now
        
        self.helper.layout = Layout(
            Field('DeviceName', autofocus="",css_class='input-sm'),
            Field('fromDate', css_class='input-sm'),
            Field('toDate', css_class='input-sm'),
            Submit('submit', _('Submit'),css_class='btn-primary center-block'),
            )

    def clean_DeviceName(self):# returns the label of the choicefield
        name=self.cleaned_data['DeviceName']
        name = dict(self.fields['DeviceName'].choices)[int(name)]        
        return name
    
    def clean_fromDate(self):
        data = self.cleaned_data['fromDate']
        now = timezone.localtime(timezone.now())
        if (now<data):
            data=now-datetime.timedelta(days=1)
        return data
        
    def clean_toDate(self):
        data = self.cleaned_data['toDate']
        now = timezone.localtime(timezone.now())
        if (now<data):
            data=now
        return data   

