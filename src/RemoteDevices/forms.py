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
import RemoteDevices.models
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field

import logging
logger = logging.getLogger("project")
                            
class DeviceForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(DeviceForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-sm-4'
        self.helper.field_class = 'col-sm-6'
#         self.helper.form_id = 'id-DeviceForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        
        self.fields['DeviceName'].label = _("Enter a name for the device")
        self.fields['DeviceCode'].label = _("Enter the code for the device")
        self.fields['DeviceIP'].label = _("Enter the IP address")
        self.fields['Type'].label = _("Select the type of the device")
        self.fields['DeviceState'].label = _("Select the status of the device")
        self.fields['Sampletime'].label = _("Set the sampletime for the device")
        
        self.helper.layout = Layout(
            Field('DeviceName', autofocus="",css_class='input-sm'),
            Field('DeviceCode', css_class='input-sm'),
            Field('DeviceIP', css_class='input-sm'),
            Field('Type', css_class='input-sm'),
            Field('DeviceState', css_class='input-sm'),
            Field('Sampletime', css_class='input-sm'),
            Submit('submit', _('Submit'),css_class='btn-primary'),
            )
        
            
    def clean_DeviceName(self):
        data = self.cleaned_data['DeviceName']
        if len(data)<=3:
           raise ValidationError(_('Invalid device name - Should have minimum 4 characters'))   
        return data
    
    def clean_DeviceIP(self):
        IP= self.cleaned_data['DeviceIP']
        try:
            for number in IP.split('.'):
                n=int(number)
        except:
            raise ValidationError(
                    _('IP address should be formatted "N1.N2.N3.N4" with Nx being numerical digits'))
        return IP

    def clean(self):
        cleaned_data=super().clean() # to use the validation of the fields from the model
        IP= cleaned_data['DeviceIP']
        Code=cleaned_data['DeviceCode']
        if int(IP.split('.')[3]) != int(Code):
            raise ValidationError(
                    _('IP address and DeviceCode mismatch. The last digit of the IP address must be equal to the DeviceCode'))
        return cleaned_data
        
    class Meta:
        model = RemoteDevices.models.DeviceModel
        fields=['DeviceName','DeviceCode','DeviceIP','Type','DeviceState','Sampletime']
    