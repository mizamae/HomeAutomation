# coding: utf-8
import datetime

from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.views import generic
from django.forms import ModelForm
import json
import Devices.BBDD
import Devices.GlobalVars
#import LocalDevices.models
#import RemoteDevices.models

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

class DeviceForm(ModelForm):
    def __init__(self, *args, **kwargs):
        initial_arguments = kwargs.get('initial', None)
        updated_initial = {}
        instance=kwargs.get('instance',None)
        if instance!=None:
            updated_initial['IO']=instance.IO
            kwargs.update(initial=updated_initial)
        super(DeviceForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-sm-4'
        self.helper.field_class = 'col-sm-6'
#         self.helper.form_id = 'id-DeviceForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        
        self.fields['DeviceName'].label = _("Enter the name for the device")
        self.fields['Type'].label = _("Select the device type")
        self.fields['IO'].label = _("Enter the GPIO for the device")
        self.fields['DeviceCode'].label = _("Enter the code for the device")
        self.fields['DeviceIP'].label = _("Enter the IP addres for the device")
        self.fields['Sampletime'].label = _("Enter the sample time for the device [s]")
        self.fields['RTsampletime'].label = _("Enter the real-time sample time for the device [s]")
        self.fields['DeviceState'].label = _("Select the state of the device")
        
        self.helper.layout = Layout(
            Field('DeviceName', css_class='input-sm'),
            Field('Type', css_class='input-sm'),
            Field('IO', css_class='input-sm'),
            Field('DeviceCode', css_class='input-sm'),
            Field('DeviceIP', css_class='input-sm'),
            Field('Sampletime', css_class='input-sm'),
            Field('RTsampletime', css_class='input-sm'),
            Field('DeviceState', css_class='input-sm'),
            Submit('submit', _('Submit'),css_class='btn-primary'),
            )
    
    def clean(self):
        cleaned_data = super(DeviceForm, self).clean()
        return cleaned_data
         
    class Meta:
        model = Devices.models.DeviceModel
        fields=['DeviceName','Type','IO','DeviceCode','DeviceIP','Sampletime','RTsampletime','DeviceState']
        
    class Media:
        js = ('DeviceFormAnimations.js',)
        
class DatagramCustomLabelsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        DV = kwargs.pop('DV')
        DGs = kwargs.pop('DGs')
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
        
        datagram_info=[]
        self.units=[]
        initial_values=[]
        for DG in DGs:
            data={}
            datagram=DG.getStructure()
            HumanNames={}
            if DV.CustomLabels=='':
                for i,name in enumerate(datagram['names']):
                    IT=Devices.models.DatagramItemModel.objects.get(pk=name.split('_')[0])
                    HumanNames[name]=IT.getHumanName()
            else:
                CustomLabels=json.loads(DV.CustomLabels)
                HumanNames=CustomLabels[DG.Identifier]
            initial_values.append(HumanNames)
            
        self.fields['DeviceName'] = forms.CharField(label=_('Name of the device'),required=True)
        self.fields['DeviceName'].initial = DV.DeviceName
        self.fields['DeviceName'].widget = forms.HiddenInput()
        self.helper.layout.append(Field('DeviceName', css_class='input-sm'))
        
        self.FieldMapping={}
        for initial,DG in zip(initial_values,DGs):
            self.FieldMapping[DG.Identifier]={}
            data=DG.getStructure()
            self.helper.layout.append(HTML("<h3><b>Datagram: "+DG.Identifier+"</b></h3>"))
            for i, field in enumerate(data['names']):
                IT=Devices.models.DatagramItemModel.objects.get(pk=int(field.split('_')[0]))
                if data['types'][i]== 'analog':
                    self.units.append(data['units'][i])
                    fieldName=DG.Identifier+'_analogvariable_%s' % i
                    self.FieldMapping[DG.Identifier][fieldName]=field
                    self.fields[fieldName] = forms.CharField(label=IT.HumanTag,required=True)                        
                    self.fields[fieldName].initial = initial[field].replace('_'+self.units[-1],'')
                    self.helper.layout.append(Field(fieldName, css_class='input-sm'))
                else:
                    self.units.append('bits')
                    fieldName=DG.Identifier+'_digitalvariable_%s' % i
                    self.helper.layout.append(HTML("<hr>"))                        
                    bitInitial=initial[field].split('$')
                    for k in range(0,8):
                        self.fields[fieldName+'_bit%s' % k] = forms.CharField(label=IT.HumanTag+ ' bit%s' % k,required=True)
                        self.FieldMapping[DG.Identifier][fieldName+'_bit%s' % k]=field
                        if len(bitInitial)==8:
                            self.fields[fieldName+'_bit%s' % k].initial = bitInitial[k]
                        else:
                            self.fields[fieldName+'_bit%s' % k].initial = fieldName+'_Bit%s' % k
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
                identifier=info[0]  # datagram identifier setup in the field name in HTML
                if not identifier in CustomLabels:
                    CustomLabels[identifier]={}
                if field.find('analog')>=0:
                    #CustomLabels[identifier].append(field_value+'_'+self.units[field_number])
                    CustomLabels[identifier][self.FieldMapping[identifier][field]]=field_value+'_'+self.units[field_number]
                    count=0
                    field_number+=1
                else:
                    if count==0:
                        #CustomLabels[identifier].append(field_value)
                        CustomLabels[identifier][self.FieldMapping[identifier][field]]=field_value
                        count=count+1
                    else:
                        #CustomLabels[identifier][-1]+='$'+field_value
                        CustomLabels[identifier][self.FieldMapping[identifier][field]]+='$'+field_value
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
        Item = cleaned_data['Item']
        return cleaned_data
    
    class Meta:
        model = Devices.models.ItemOrdering
        fields=['order','Item']
        
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
        
        DVs=Devices.models.DeviceModel.objects.all()
        device_list=[(1,_('Main Unit'))]
        i=2
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

