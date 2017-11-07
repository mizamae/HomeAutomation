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

class inlineDailyForm(ModelForm):  
    def __init__(self, *args, **kwargs):
        super(inlineDailyForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field.find('Hour')>=0:
                self.fields[field].label=field.replace('Hour','') + ' H'
        
    def clean(self):
        cleaned_data=super().clean() # to use the validation of the fields from the model
        return cleaned_data
    
    class Meta:
        model = HomeAutomation.models.inlineDaily
        fields=['Day','Hour0','Hour1','Hour2','Hour3','Hour4','Hour5','Hour6','Hour7','Hour8','Hour9','Hour10'
                ,'Hour11','Hour12','Hour13','Hour14','Hour15','Hour16','Hour17','Hour18','Hour19','Hour20','Hour21','Hour22','Hour23']

class AutomationRuleForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(AutomationRuleForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-sm-4'
        self.helper.field_class = 'col-sm-6'
#         self.helper.form_id = 'id-DeviceForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        
        self.fields['Identifier'].label = _("Set the name for the automation rule")
        self.fields['Active'].label = _("Activate the rule")
        self.fields['PreviousRule'].label = _("Enter the previous rule to be chained")
        self.fields['Operator1'].label = _("Enter the operator between the preious rule and this one")
        self.fields['Var1'].label = _("Enter the first variable in the rule")
        self.fields['Operator12'].label = _("Enter the operator between the first and second variable")
        self.fields['Var2'].label = _("Enter the second variable in the rule")
        self.fields['FrequencyCheck'].label = _("Set the frequency check")
                
        self.helper.layout = Layout(
            Field('Identifier', css_class='input-sm'),
            Field('Active', css_class='input-sm'),
            Field('PreviousRule', css_class='input-sm'),
            Field('Operator1', css_class='input-sm'),
            Field('Var1', css_class='input-sm'),
            Field('Operator12', css_class='input-sm'),
            Field('Var2', css_class='input-sm'),
            Field('FrequencyCheck', css_class='input-sm'),
            Submit('submit', _('Submit'),css_class='btn-primary'),
            )
        
    class Meta:
        model = HomeAutomation.models.AutomationRuleModel
        fields=['Identifier','Active','PreviousRule','Operator1','Var1','Operator12','Var2','FrequencyCheck']                