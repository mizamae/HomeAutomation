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
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field,Fieldset

import Tracks.models

import logging
logger = logging.getLogger("project")


    
                                       
class BeaconForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(BeaconForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper()
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-sm-4'
        self.helper.field_class = 'col-sm-6'
#         self.helper.form_id = 'id-DeviceForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
         
        self.fields['Identifier'].label = _("Set the unique name for the beacon")
        self.fields['Latitude'].label = _("Enter the latitude of the beacon")
        self.fields['Longitude'].label = _("Enter the longitude of the beacon")

        self.helper.layout = Layout(
                Field('Identifier', css_class='input-sm'),
                Field('Latitude', css_class='input-sm'),
                Field('Longitude', css_class='input-sm'),)
        
    class Meta:
        model = Tracks.models.BeaconModel
        
        fields=['Identifier','Latitude','Longitude']
    class Media:
        js = ('GoogleMapsLatLong.js',)

