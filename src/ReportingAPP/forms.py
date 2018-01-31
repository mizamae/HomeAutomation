# coding: utf-8
import datetime

from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.views import generic
from django.forms import ModelForm
from django.urls import reverse

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
        model = models.ReportModel
        fields=['ReportTitle','Periodicity','DataAggregation']