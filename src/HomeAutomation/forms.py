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
import Master_GPIOs.models
#import RemoteDevices.models
import Devices.models

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
        self.fields['Datatype'].label = _("Set the datatype of the variable")
        self.fields['Datatype'].label = _("Enter the value of the variable")
        self.fields['Units'].label = _("Set the units of the variable")
        
        self.helper.layout = Layout(
            Field('Label', css_class='input-sm'),
            Field('Label', css_class='input-sm'),
            Field('Value', css_class='input-sm'),
            Field('Units', css_class='input-sm'),
            Submit('submit', _('Submit'),css_class='btn-primary'),
            )
        
    class Meta:
        model = HomeAutomation.models.MainDeviceVarModel
        fields=['Label','Datatype','Value','Units']

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
        
class BaseAutomationRuleForm(ModelForm):
    """
    
    """
    def __init__(self, *args, **kwargs):
        super(BaseAutomationRuleForm, self).__init__(*args, **kwargs)
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
        self.fields['PreviousRule'].queryset = HomeAutomation.models.AutomationRuleModel.objects.exclude(pk__exact=self.instance.pk)
        self.fields['Operator1'].label = _("Enter the operator between the previous rule and this one")
        self.fields['Var1'].label = _("Enter the first variable in the rule")
        self.fields['Operator12'].label = _("Enter the operator between the first and second variable")
        self.fields['Var2'].label = _("Enter the second variable in the rule")
        self.fields['Var2Hyst'].label = _("Enter the hysteresis margin")
                
        self.helper.layout = Layout(
            Field('Identifier', css_class='input-sm'),
            Field('Active', css_class='input-sm'),
            Field('PreviousRule', css_class='input-sm'),
            Field('Operator1', css_class='input-sm'),
            Field('Var1', css_class='input-sm'),
            Field('Operator12', css_class='input-sm'),
            Field('Var2', css_class='input-sm'),
            Field('Var2Hyst', css_class='input-sm'),
            )
        self.helper.layout.append(Field('ActionType', css_class='input-sm'))
        self.helper.layout.append(Submit('submit', _('Save'),css_class='btn-primary'))
        
    class Meta:
        model = HomeAutomation.models.AutomationRuleModel
        fields=['Identifier','Active','PreviousRule','Operator1','Var1','Operator12','Var2','Var2Hyst','Action']
        widgets = {'Action': forms.HiddenInput()}
        
class AutomationRuleForm(BaseAutomationRuleForm):
    ACTION_CHOICES=(
        ('a',_('Activate output on Main')),
        ('b',_('Send command to a device')),
        ('c',_('Send an email')),
    )
    ActionType = forms.ChoiceField(choices=ACTION_CHOICES,label=_('Select the action'))
    IO=forms.ModelChoiceField(queryset=Master_GPIOs.models.IOmodel.objects.filter(direction='OUT'),label=_('Select the output'),required = False)
    IOValue=forms.ChoiceField(choices=Master_GPIOs.models.IOmodel.VALUE_CHOICES,label=_('Select the output value when the rule is True'),required = False)
    Device=forms.ModelChoiceField(queryset=Devices.models.DeviceModel.objects.filter(Type__Connection='REMOTE'),label=_('Select the device to send the order to'),required = False)
    Order=forms.ModelChoiceField(queryset=Devices.models.CommandModel.objects.all(),label=_('Select the order to send'),required = False)
    
    def __init__(self, *args, **kwargs):
        initial_arguments = kwargs.get('initial', None)
        updated_initial = {}
        instance=kwargs.get('instance',None)
        if instance!=None and instance.Action!='':
            Action=json.loads(instance.Action)
            updated_initial['ActionType']=Action['ActionType']
            updated_initial['IO']=Action['IO']
            updated_initial['IOValue']=Action['IOValue']
            updated_initial['Device']=Action['Device']
            updated_initial['Order']=Action['Order']
            kwargs.update(initial=updated_initial)
        super(AutomationRuleForm, self).__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super(AutomationRuleForm, self).clean()
        action = cleaned_data.get('Action')
        ActionType = cleaned_data.get('ActionType')
        IO = cleaned_data.get('IO')
        IOValue = cleaned_data.get('IOValue')
        Device = cleaned_data.get('Device')
        Order = cleaned_data.get('Order')
        
        if IO!=None:
            IO=IO.pk
        if Device!=None:
            Device=Device.pk
        if Order!=None:
            Order=Order.pk
            
        data={'ActionType':ActionType,'IO':IO,'IOValue':IOValue,'Device':Device,'Order':Order}
        
        cleaned_data.update(Action=json.dumps(data))
        return cleaned_data
         
    class Meta(BaseAutomationRuleForm.Meta):
        fields=BaseAutomationRuleForm.Meta.fields + ['ActionType','IO','Device','Order']
        
    class Media:
        js = ('AutomationRuleFormAnimations.js',)
        
        