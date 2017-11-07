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
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field,Fieldset

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
        datagram_info = kwargs.pop('datagram_info')
        super(DatagramCustomLabelsForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-sm-4'
        self.helper.field_class = 'col-sm-6'
        self.helper.form_id = 'DatagramCustomLabelsForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout()
        
        DeviceName=datagram_info[0]['DeviceName']
            
        self.fields['DeviceName'] = forms.CharField(label=_('Name of the device'),required=True)
        self.fields['DeviceName'].initial = DeviceName
        self.fields['DeviceName'].widget = forms.HiddenInput()
        self.helper.layout.append(Field('DeviceName', css_class='input-sm'))
        
        self.units=[]
        for data in datagram_info:
            fields=data['fields']
            types=data['types']
            identifier=data['ID']
            self.helper.layout.append(HTML("<h3><b>Datagram: "+identifier+"</b></h3>"))
            for i, field in enumerate(fields):
                
                if types[i]== 'analog':
                    self.units.append(data['fields'][i].split('_')[-1])
                    fieldName=identifier+'_analogvariable_%s' % i
                    self.fields[fieldName] = forms.CharField(label=field,required=True)
                    self.fields[fieldName].initial = data['initial_values'][i].replace('_'+self.units[-1],'')
                    self.helper.layout.append(Field(fieldName, css_class='input-sm'))
                else:
                    self.units.append('bits')
                    fieldName=identifier+'_digitalvariable_%s' % i
                    self.helper.layout.append(HTML("<hr>"))
                    initial_values=data['initial_values'][i].split('$')
                    for k in range(0,8):
                        self.fields[fieldName+'_bit%s' % k] = forms.CharField(label=field+ ' bit%s' % k,required=True)
                        if len(initial_values)==8:
                            self.fields[fieldName+'_bit%s' % k].initial = initial_values[k]
                        else:
                            self.fields[fieldName+'_bit%s' % k].initial = 'Bit%s' % k
                        self.helper.layout.append(fieldName+'_bit%s' % k)
                    self.helper.layout.append(HTML("<hr>"))
            self.helper.layout.append(HTML("<h2></h2>"))
        self.helper.layout.append(Submit('submit', _('Save'),css_class='btn-primary'))
        
    def get_variablesLabels(self):
        CustomLabels={}
        count=0
        field_number=0
        for field in self.fields:
            if field.find('variable')>=0:
                field_value=self.cleaned_data[field]
                info=field.split('_')
                identifier=info[0]
                if not identifier in CustomLabels:
                    CustomLabels[identifier]=[]
                if field.find('analog')>=0:
                    CustomLabels[identifier].append(field_value+'_'+self.units[field_number])
                    count=0
                    field_number+=1
                else:
                    if count==0:
                        CustomLabels[identifier].append(field_value)
                        count=count+1
                    else:
                        CustomLabels[identifier][-1]+='$'+field_value
                        count=count+1
                
                if count>=8:
                    count=0
                    field_number+=1
        return CustomLabels
                
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

