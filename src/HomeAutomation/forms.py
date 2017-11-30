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
        self.fields['PlotType'].label = _("Set the type of plot for the variable")
        
        self.helper.layout = Layout(
            Field('Label', css_class='input-sm'),
            Field('Label', css_class='input-sm'),
            Field('Value', css_class='input-sm'),
            Field('Units', css_class='input-sm'),
            Field('PlotType', css_class='input-sm'),
            Submit('submit', _('Submit'),css_class='btn-primary'),
            )
        
    class Meta:
        model = HomeAutomation.models.MainDeviceVarModel
        fields=['Label','Datatype','Value','Units','PlotType']

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
        
class RuleItemForm(ModelForm):  
    def __init__(self, *args, **kwargs):
        super(RuleItemForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-sm-4'
        self.helper.field_class = 'col-sm-6'
#         self.helper.form_id = 'id-DeviceForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        self.fields['order'].label = _("Execution order")
        self.fields['PreVar1'].label = _("Prefix for the first term")
        self.fields['Var1'].label = _("First term")
        self.fields['Operator12'].label = _("Operator")
        self.fields['PreVar2'].label = _("Prefix for the second term")
        self.fields['Var2'].label = _("Second term")
        self.fields['IsConstant'].label = _("Second term is a constant")
        self.fields['Constant'].label = _("Constant value")
        self.fields['Var2Hyst'].label = _("Hysteresis value")
        self.fields['Operator3'].label = _("Operator with the next rule")

    def clean(self):
         cleaned_data = super(RuleItemForm, self).clean()
         IsConstant = cleaned_data.get('IsConstant')
         Constant = cleaned_data.get('Constant')
         Var2 = cleaned_data.get('Var2')
         if IsConstant==True :
             cleaned_data.update(Var2=None)
             if Constant==None:
                 raise ValidationError({'Constant':_("This field cannot be left empty if 'IsConstant' has been selected")})
         else:
            if Var2==None:
                 raise ValidationError({'Var2':_("This field cannot be left empty if 'IsConstant' is not selected")})
         return cleaned_data
         
    class Meta:
        model = HomeAutomation.models.RuleItem
        fields=['order','PreVar1','Var1','Operator12','PreVar2','Var2','IsConstant','Constant','Var2Hyst','Operator3']
        
    
class AutomationRuleForm(ModelForm):
    ACTION_CHOICES=(
        ('a',_('Activate output on Main')),
        ('b',_('Send command to a device')),
        ('c',_('Send an email')),
        ('z',_('None')),
    )
    
    ActionType = forms.ChoiceField(choices=ACTION_CHOICES,label=_('Select the action'))
    IO=forms.ModelChoiceField(queryset=Master_GPIOs.models.IOmodel.objects.filter(direction='OUT'),label=_('Select the output'),required = False)
    IOValue=forms.ChoiceField(choices=Master_GPIOs.models.IOmodel.VALUE_CHOICES,label=_('Select the output value when the rule is True'),required = False,initial=0)
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
        self.helper = FormHelper(self)
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-sm-4'
        self.helper.field_class = 'col-sm-6'
#         self.helper.form_id = 'id-DeviceForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        self.fields['Identifier'].label = _("Set the name for the automation rule")
        self.fields['Active'].label = _("Activate the rule")
        self.fields['OnError'].label = _("Select the output value in case of error")
        self.fields['PreviousRule'].label = _("Select the previous rule to be chained")
        self.fields['PreviousRule'].queryset=HomeAutomation.models.AutomationRuleModel.objects.filter(Action__contains='"ActionType": "z"')
        self.fields['OperatorPrev'].label = _("Select the operator between the previous rule and this one")
        self.helper.layout = Layout(
            Field('Identifier', css_class='input-sm'),
            Field('Active', css_class='input-sm'),
            Field('OnError', css_class='input-sm'),
            )
        self.helper.layout.append(Field('ActionType', css_class='input-sm'))
        self.helper.layout.append(Field('IO', css_class='input-sm'))
        self.helper.layout.append(Field('IOValue', css_class='input-sm'))
        self.helper.layout.append(Field('Device', css_class='input-sm'))
        self.helper.layout.append(Field('Order', css_class='input-sm'))
        self.helper.layout.append(Submit('submit', _('Save'),css_class='btn-primary'))
    
    def clean(self):
         cleaned_data = super(AutomationRuleForm, self).clean()
         action = cleaned_data.get('Action')
         ActionType = cleaned_data.get('ActionType')
         IO = cleaned_data.get('IO')
         IOValue = cleaned_data.get('IOValue')
         Device = cleaned_data.get('Device')
         Order = cleaned_data.get('Order')
         PreviousRule= cleaned_data.get('PreviousRule')
         OperatorPrev= cleaned_data.get('OperatorPrev')
         if PreviousRule!=None:
             if OperatorPrev==None:
                 raise ValidationError({'OperatorPrev':_("This field cannot be left empty if a previous rule has been selected")})
         if ActionType=='a':
             Device=None
             Order=None
             if IO==None:
                 raise ValidationError({'IO':_("This field cannot be left empty if 'Activate output on Main' is selected as action")})
         elif ActionType=='b':
             IO=None
             IOValue=None
             if Device==None:
                 raise ValidationError({'Device':_("This field cannot be left empty if Send command to a device is selected as action")})
             else:
                 if Order==None:
                     raise ValidationError({'Order':_("This field cannot be left empty if Send command to a device is selected as action")})
         elif ActionType=='z':
            IO=None
            IOValue=None
            Device=None
            Order=None
                      
         if IO!=None:
             IO=IO.pk
         if Device!=None:
             Device=Device.pk
         if Order!=None:
             Order=Order.pk
             
         data={'ActionType':ActionType,'IO':IO,'IOValue':IOValue,'Device':Device,'Order':Order}
         
         cleaned_data.update(Action=json.dumps(data))
         return cleaned_data
         
    class Meta:
        fields=['Identifier','Active','OnError','PreviousRule','OperatorPrev','Action']
        widgets = {'Action': forms.HiddenInput()}
        model = HomeAutomation.models.AutomationRuleModel
        
    class Media:
        js = ('AutomationRuleFormAnimations.js',)
        
        