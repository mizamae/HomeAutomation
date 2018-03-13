# coding: utf-8
import datetime

from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.views import generic
from django.forms import ModelForm,HiddenInput
from django.urls import reverse

from . import models
from .constants import APP_TEMPLATE_NAMESPACE

from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FormActions,AppendedText
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field,Fieldset

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
        self.fields['ContentJSON'].widget = HiddenInput()
        
        buttons=FormActions(
                    #Submit('edit', _('Save changes')),
                    HTML('<a id="submit-id-edit" onclick="SaveReport();" class="btn btn-primary">'+str(_('Save'))+'</a>'),
                    HTML('<a href="{% url "'+APP_TEMPLATE_NAMESPACE+':home" %}" class="btn btn-secondary">'+str(_('Cancel'))+'</a>')
                )
        
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class':'input-sm has-popover', 'data-content':help_text, 'data-placement':'right', 'data-container':'body'})
            else:
                self.fields[field].widget.attrs.update({'class':'input-sm '})
                
        self.helper.layout = Layout(
            Field('Title'),
            Field('Periodicity'),
            Field('DataAggregation'),
            buttons
            )
    
    def save(self):
        instance=super().save(commit=False)
        instance.store2DB()
        return instance
        
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
        fields=['Title','Periodicity','DataAggregation','ContentJSON']
        
