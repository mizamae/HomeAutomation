# coding: utf-8
import datetime

from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.views import generic
from django.forms import ModelForm

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field

import HomeAutomation.models

import logging
logger = logging.getLogger("project")
                               
class MainDeviceVarForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(MainDeviceVarForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-sm-4'
        self.helper.field_class = 'col-sm-6'
#         self.helper.form_id = 'id-DeviceForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        
        self.fields['Label'].label = _("Set the label for the variable")
        self.fields['Value'].label = _("Enter the value of the variable")
        self.fields['Units'].label = _("Set the units of the variable")
        
        self.helper.layout = Layout(
            Field('Label', css_class='input-sm'),
            Field('Value', css_class='input-sm'),
            Field('Units', css_class='input-sm'),
            Submit('submit', _('Submit'),css_class='btn-primary'),
            )
        
    class Meta:
        model = HomeAutomation.models.MainDeviceVarModel
        fields=['Label','Value','Units']


