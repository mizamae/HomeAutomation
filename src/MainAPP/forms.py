# coding: utf-8
import datetime

from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.views import generic
from django.forms import ModelForm
from django.contrib.auth import get_user_model

import json
import DevicesAPP.models
from DevicesAPP.constants import REMOTE_TCP_CONNECTION as DevicesAPP_REMOTE_TCP_CONNECTION,GPIO_OUTPUT

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field,Fieldset
from crispy_forms.bootstrap import AppendedText

from . import models
from .constants import AUTOMATION_ACTION_CHOICES

import logging
logger = logging.getLogger("project")

FORMS_LABEL_CLASS='col-lg-5 col-md-5 col-sm-12 col-xs-12'
FORMS_FIELD_CLASS='col-lg-5 col-md-5 col-sm-12 col-xs-12'

class SiteSettingsForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(SiteSettingsForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        self.helper.labels_uppercase = True
        self.helper.label_class = FORMS_LABEL_CLASS
        self.helper.field_class = FORMS_FIELD_CLASS
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            self.fields[field].widget.attrs.update({'onblur':'checkIfChanged('+str(field)+')'})
            if help_text != '':
                self.fields[field].widget.attrs.update({'class':'input-sm has-popover', 'data-content':help_text, 'data-placement':'right', 'data-container':'body'})
            else:
                self.fields[field].widget.attrs.update({'class':'input-sm ','readonly':True})
                
        self.helper.layout = Layout(
            Fieldset(_('General'),
                     Field('FACILITY_NAME'),
                     Field('SITE_DNS'),
                     Field('VERSION_AUTO_DETECT'),
                     Field('VERSION_AUTO_UPDATE'),
                     Field('VERSION_CODE'),
                     Field('VERSION_DEVELOPER'),
                     AppendedText('NTPSERVER_RESTART_TIMEDELTA', 'min'),
                ),
            Fieldset(_('Slaves WIFI network'),
                     Field('WIFI_SSID'),
                     Field('WIFI_PASSW'),
                     Field('WIFI_IP'),
                     Field('WIFI_MASK'),
                     Field('WIFI_GATE'),
                ),
            Fieldset(_('LAN network'),
                     Field('ETH_IP'),
                     Field('ETH_MASK'),
                     Field('ETH_GATE'),
                ),
            Fieldset(_('Security'),
                     Field('PROXY_AUTO_DENYIP'),
                     Field('AUTODENY_ATTEMPTS'),
                     Field('PROXY_CREDENTIALS'),
                     Field('PROXY_USER1'),
                     Field('PROXY_PASSW1'),
                     Field('PROXY_USER2'),
                     Field('PROXY_PASSW2'),
                ),
            Fieldset(_('Telegram Features'),
                     Field('TELEGRAM_TOKEN'),
                     Field('TELEGRAM_CHATID'),
                ),
            Fieldset(_('OpenWeatherMap Features'),
                     Field('OWM_TOKEN'),
                ),
            Fieldset(_('REE ESIOS Features'),
                     Field('ESIOS_TOKEN'),
                ),
            Fieldset(_('Iberdrola Features'),
                     Field('IBERDROLA_USER'),
                     Field('IBERDROLA_PASSW')
                ),
            Submit('submit', _('Save'),css_class='btn-primary'),
            )
     
    def save(self, *args, **kwargs):
        instance=super().save(commit=False)
        instance.store2DB(update_fields=self.changed_data)
        return instance
        
    def clean(self):
        cleaned_data=super().clean() # to use the validation of the fields from the model
        VERSION_AUTO_DETECT = cleaned_data['VERSION_AUTO_DETECT']
        if not VERSION_AUTO_DETECT:
            cleaned_data.update(VERSION_AUTO_UPDATE=False)
        return cleaned_data
     
    class Meta:
        model = models.SiteSettings
        exclude=[]
        #widgets = {
        #    'WIFI_PASSW': forms.PasswordInput(render_value=True),
        #}
    class Media:
        js = ('SiteSettingsFormAnimations.js',)
        
class AdditionalCalculationsForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(AdditionalCalculationsForm, self).__init__(*args, **kwargs)
        # If you pass FormHelper constructor a form instance
        # It builds a default layout with all its fields
        self.helper = FormHelper(self)
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-sm-6'
        self.helper.field_class = 'col-sm-6'
#         self.helper.form_id = 'id-DeviceForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
         
        self.fields['SourceVar'].label = _("Select the source variable")        
        self.fields['Timespan'].label = _("Select the time-span for the calculation")
        self.fields['Periodicity'].label = _("Select the calculation update frequency")
        self.fields['Calculation'].label = _("Select the calculation")
        self.fields['Delay'].label = _("Set the number of hours for the delay of the calculation")
         
        self.helper.layout = Layout(
            Field('SourceVar', css_class='input-sm'),
            Field('Timespan', css_class='input-sm'),
            Field('Periodicity', css_class='input-sm'),
            Field('Calculation', css_class='input-sm'),
            Field('Delay', css_class='input-sm'),
            Submit('submit', _('Submit'),css_class='btn-primary'),
            )
     
    def save(self, *args, **kwargs):
        instance=super().save(commit=False)
        instance.store2DB()
        return instance
        
    def clean(self):
        cleaned_data=super().clean() # to use the validation of the fields from the model
        Periodicity = cleaned_data['Periodicity']
        Timespan = cleaned_data['Timespan']
        SourceVar = cleaned_data['SourceVar']
        Calculation = cleaned_data['Calculation']
        return cleaned_data
     
    class Meta:
        model = models.AdditionalCalculations
        fields=['SourceVar','Timespan','Periodicity','Calculation','Delay']
        
class inlineDailyForm(ModelForm):  
    def __init__(self, *args, **kwargs):
        instance=kwargs.get('instance',None)
        super(inlineDailyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        for field in self.fields:
            if field.find('Hour')>=0:
                self.fields[field].label=field.replace('Hour','') + ' H'
                #self.fields[field].widget.attrs['size']=8
                    
        if instance!=None:
            self.fields['Day'].widget.attrs['hidden'] = True
                    
        CSS_CLASS_DAY='col-md-2 col-xs-3'
        CSS_CLASS_HOUR='col-md-2 col-xs-3'
        self.helper.layout = Layout(
                Div(
                    Div(Field('Day'), css_class=CSS_CLASS_DAY),
                    Div(Field('Hour0'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour1'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour2'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour3'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour4'), css_class=CSS_CLASS_HOUR),
                    css_class='row-fluid'  # here you can add some custom class, for example 'row-fluid margin-top-15'
                ),
                Div(
                    Div(Field('Hour5'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour6'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour7'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour8'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour9'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour10'), css_class=CSS_CLASS_HOUR),
                    css_class='row-fluid'  # here you can add some custom class, for example 'row-fluid margin-top-15'
                ),
                Div(
                    Div(Field('Hour11'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour12'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour13'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour14'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour15'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour16'), css_class=CSS_CLASS_HOUR),
                    css_class='row-fluid'  # here you can add some custom class, for example 'row-fluid margin-top-15'
                ),
                Div(
                    Div(Field('Hour17'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour18'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour19'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour20'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour21'), css_class=CSS_CLASS_HOUR),
                    Div(Field('Hour22'), css_class=CSS_CLASS_HOUR),
                    css_class='row-fluid'  # here you can add some custom class, for example 'row-fluid margin-top-15'
                ),
                Div(
                    Div(Field('Hour23'), css_class=CSS_CLASS_HOUR),
                    css_class='row-fluid'  # here you can add some custom class, for example 'row-fluid margin-top-15'
                ),
            )
        
        
    def clean(self):
        cleaned_data=super().clean() # to use the validation of the fields from the model
        return cleaned_data
    
    class Meta:
        model = models.inlineDaily
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
        self.fields['Order'].label = _("Execution order")
        self.fields['PreVar1'].label = _("Prefix for the variable")
        self.fields['Var1'].label = _("Variable")
        self.fields['Operator12'].label = _("Operator")
        self.fields['PreVar2'].label = _("Prefix for the setpoint")
        self.fields['Var2'].label = _("Setpoint")
        self.fields['IsConstant'].label = _("Setpoint is a constant")
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
        model = models.RuleItems
        fields=['Order','PreVar1','Var1','Operator12','PreVar2','Var2','IsConstant','Constant','Var2Hyst','Operator3']
        
    
class AutomationRuleForm(ModelForm):
    
    ActionType = forms.ChoiceField(choices=AUTOMATION_ACTION_CHOICES,label=_('Select the action'))
    Users = forms.ModelMultipleChoiceField(queryset=get_user_model().objects.all(),
                              label=_('Select the user to send the email to'),required = False)
    IO=forms.ModelChoiceField(queryset=DevicesAPP.models.MasterGPIOs.objects.filter(Direction=GPIO_OUTPUT),
                              label=_('Select the output'),required = False)
    IOValue=forms.ChoiceField(choices=DevicesAPP.constants.GPIOVALUE_CHOICES,
                              label=_('Select the output value when the rule is True'),required = False,initial=0)
    Device=forms.ModelChoiceField(queryset=DevicesAPP.models.Devices.objects.filter(DVT__Connection=DevicesAPP_REMOTE_TCP_CONNECTION),
                                  label=_('Select the device to send the order to'),required = False)
    Order=forms.ModelChoiceField(queryset=DevicesAPP.models.DeviceCommands.objects.all(),
                                 label=_('Select the order to send'),required = False)
    NotificationTrue=forms.BooleanField(label=_('Send notification when the rule evaluates to True'),required = False)
    NotificationFalse=forms.BooleanField(label=_('Send notification when the rule evaluates to False'),required = False)
    
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
            updated_initial['NotificationTrue']=Action.get('NotificationTrue',False)
            updated_initial['NotificationFalse']=Action.get('NotificationFalse',False)
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
        self.fields['OnError'].label = _("Select the rule evaluation in case of error")
        self.fields['EdgeExec'].label = _("Execute rule only on the transitions from FALSE to TRUE and viceversa")
        self.fields['PreviousRule'].label = _("Select the previous rule to be chained")
        self.fields['PreviousRule'].queryset=models.AutomationRules.objects.filter(Action__contains='"ActionType": "z"')
        self.fields['OperatorPrev'].label = _("Select the operator between the previous rule and this one")
        self.helper.layout = Layout(
            Field('Identifier', css_class='input-sm'),
            Field('Active', css_class='input-sm'),
            Field('OnError', css_class='input-sm'),
            Field('EdgeExec', css_class='input-sm'),
            )
        self.helper.layout.append(Field('ActionType', css_class='input-sm'))
        self.helper.layout.append(Field('IO', css_class='input-sm'))
        self.helper.layout.append(Field('IOValue', css_class='input-sm'))
        self.helper.layout.append(Field('Device', css_class='input-sm'))
        self.helper.layout.append(Field('Order', css_class='input-sm'))
        self.helper.layout.append(Field('NotificationTrue', css_class='input-sm'))
        self.helper.layout.append(Field('NotificationFalse', css_class='input-sm'))
        self.helper.layout.append(Submit('submit', _('Save'),css_class='btn-primary'))
    
    def clean(self):
         cleaned_data = super(AutomationRuleForm, self).clean()
         action = cleaned_data.get('Action')
         EdgeExec=cleaned_data.get('EdgeExec')
         ActionType = cleaned_data.get('ActionType')
         IO = cleaned_data.get('IO')
         IOValue = cleaned_data.get('IOValue')
         Device = cleaned_data.get('Device')
         Order = cleaned_data.get('Order')
         PreviousRule= cleaned_data.get('PreviousRule')
         OperatorPrev= cleaned_data.get('OperatorPrev')
         NotificationTrue= cleaned_data.get('NotificationTrue',False)
         NotificationFalse= cleaned_data.get('NotificationFalse',False)
         cleaned_data.update(NotificationFalse=NotificationFalse)
         if PreviousRule!=None:
             if OperatorPrev==None:
                 raise ValidationError({'OperatorPrev':_("This field cannot be left empty if a previous rule has been selected")})
         if ActionType=='a': # activate Main device IO
             Device=None
             Order=None
             if IO==None:
                 raise ValidationError({'IO':_("This field cannot be left empty if 'Activate output on Main' is selected as action")})
         elif ActionType=='b': # send an order to a device
             IO=None
             IOValue=None
             if Device==None:
                 raise ValidationError({'Device':_("This field cannot be left empty if Send command to a device is selected as action")})
             else:
                 if Order==None:
                     raise ValidationError({'Order':_("This field cannot be left empty if Send command to a device is selected as action")})
             cleaned_data.update(EdgeExec=True)
         elif ActionType=='c': # send email
             Device=None
             Order=None
             IO==None
             if IO==None:
                 raise ValidationError({'IO':_("This field cannot be left empty if 'Activate output on Main' is selected as action")})
             cleaned_data.update(EdgeExec=True)
         elif ActionType=='z': # no action
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
             
         data={'ActionType':ActionType,'IO':IO,'IOValue':IOValue,'Device':Device,'Order':Order,'NotificationTrue':NotificationTrue,'NotificationFalse':NotificationFalse}
         
         cleaned_data.update(Action=json.dumps(data))
         return cleaned_data
         
    class Meta:
        fields=['Identifier','Active','OnError','EdgeExec','PreviousRule','OperatorPrev','Action']
        widgets = {'Action': forms.HiddenInput()}
        model = models.AutomationRules
        
    class Media:
        js = ('AutomationRuleFormAnimations.js',)
        
        