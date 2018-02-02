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

from . import models

FORMS_LABEL_CLASS='col-lg-5 col-md-5 col-sm-12 col-xs-12'
FORMS_FIELD_CLASS='col-lg-5 col-md-5 col-sm-12 col-xs-12'

class ReportsForm(ModelForm):  
    
    def __init__(self, *args, **kwargs):
        super(ReportsForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        #self.helper.labels_uppercase = True
        self.helper.label_class = FORMS_LABEL_CLASS
        self.helper.field_class = FORMS_FIELD_CLASS

        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        
        self.fields['Title'].label = _('Title of the report')
        self.fields['Periodicity'].label = _('Set the periodicity')
        self.fields['DataAggregation'].label = _('Set the aggregation of the data')
        
        self.helper.layout = Layout(
            Field('Title', css_class='input-sm'),
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
        model = models.Reports
        fields=['Title','Periodicity','DataAggregation']
        
