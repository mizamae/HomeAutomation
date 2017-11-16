# coding: utf-8
import datetime

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.forms import ModelForm

import LocalDevices.models
from Master_GPIOs.models import IOmodel

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
        
        self.fields['DeviceName'].label = _("Enter the name of the sensor")
        self.fields['IO'].label = _("Select the GPIO linked to the sensor")
        self.fields['IO'].queryset=IOmodel.objects.filter(direction='SENS')
        self.fields['Type'].label = _("Select the type of the sensor")
        self.fields['DeviceState'].label = _("Activate the polling of the sensor")
        self.fields['Sampletime'].label = _("Set the sample time for the measurement [s]")
        #self.fields['RTsampletime'].label = _("Set the sample time for real-time polling [s]")
        
        self.helper.layout = Layout(
            Field('DeviceName', css_class='input-sm'),
            Field('IO', autofocus="",css_class='input-sm'),
            Field('Type', css_class='input-sm'),
            Field('DeviceState', css_class='input-sm'),
            Field('Sampletime', css_class='input-sm'),
            #Field('RTsampletime', css_class='input-sm'),
            Submit('submit', _('Submit'),css_class='btn-primary'),
            )
 
    class Meta:
        model = LocalDevices.models.DeviceModel
        fields=['DeviceName','IO','Type','DeviceState','Sampletime']#,'RTsampletime']
        
