from django.db.models import Q
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.utils.functional import lazy
import datetime
import sys
import os
import json
from Events.consumers import PublishEvent

from django.dispatch import receiver
from django.db.models.signals import pre_save,post_save,post_delete,pre_delete

import Devices.GlobalVars
import Devices.BBDD

import Master_GPIOs.models

import logging

logger = logging.getLogger("project")
                                           
class MainDeviceVarModel(models.Model):
    DATATYPE_CHOICES=(
        (0,_('Float')),
        (1,_('Integer'))
    )
    PLOTTYPE_CHOICES=(
        ('line',_('Hard Line')),
        ('spline',_('Smoothed Line')),
        ('column',_('Bars')),
    )
    Label = models.CharField(max_length=50,unique=True)
    Value = models.DecimalField(max_digits=6, decimal_places=2)
    Datatype=models.PositiveSmallIntegerField(choices=DATATYPE_CHOICES,default=0)
    PlotType= models.CharField(max_length=10,choices=PLOTTYPE_CHOICES,default='line')
    Units = models.CharField(max_length=10)
    
    __original_Value = None
    
    def __str__(self):
        return self.Label
    
    def __init__(self, *args, **kwargs):
        super(MainDeviceVarModel, self).__init__(*args, **kwargs)
        self.__original_Value = self.Value
        
    def save(self, *args, **kwargs):
        if self.Value != self.__original_Value and self.__original_Value != '':
            registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                       configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')
            timestamp=timezone.now()-datetime.timedelta(seconds=1) #para hora con info UTC
            registerDB.insert_VARs_register(TimeStamp=timestamp)
            #logger.info('Se ha modificado la variable local ' + str(self) + ' del valor ' + str(self.__original_Value))
        self.__original_Value = self.Value
        super(MainDeviceVarModel, self).save(*args, **kwargs)
        
    def updateAutomationVars(self):
        AutomationVars=AutomationVariablesModel.objects.filter(Device='Main')
        
        dvar={'Label':self.Label,'Tag':self.pk,'Device':'Main','Table':'MainVariables','BitPos':None}
        try:
            avar=AutomationVars.get(Tag=dvar['Tag'],Table=dvar['Table'],BitPos=dvar['BitPos'])
        except:
            avar=None
            
        if avar!=None:
            avar.Label=dvar['Label']
        else:
            avar=AutomationVariablesModel()
            avar.Label=dvar['Label']
            avar.Device=dvar['Device']
            avar.Tag=dvar['Tag']
            avar.Table=dvar['Table']
            avar.BitPos=dvar['BitPos']
        avar.save()
        
    class Meta:
        verbose_name = _('Main device var')
        verbose_name_plural = _('Main device vars')   
        
@receiver(post_save, sender=MainDeviceVarModel, dispatch_uid="update_MainDeviceVarModel")
def update_MainDeviceVarModel(sender, instance, update_fields,**kwargs):
    timestamp=timezone.now() #para hora con info UTC
    registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                           configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')
    
    if not kwargs['created']:   # an instance has been modified
        #logger.info('Se ha modificado la variable local ' + str(instance) + ' al valor ' + str(instance.Value))
        PublishEvent(Severity=0,Text=str(_('Variable '))+instance.Label+str(_(' has changed. Current value is '))+str(instance.Value) + str(instance.Units))
    else:
        logger.info('Se ha creado la variable local ' + str(instance))
        registerDB.check_IOsTables()
    
    registerDB.insert_VARs_register(TimeStamp=timestamp)
    instance.updateAutomationVars()
    
class MainDeviceVarWeeklyScheduleModel(models.Model):
    Label = models.CharField(max_length=50,unique=True)
    Active = models.BooleanField(default=False)
    Var = models.ForeignKey(MainDeviceVarModel,on_delete=models.CASCADE)
    LValue = models.DecimalField(max_digits=6, decimal_places=2)
    HValue = models.DecimalField(max_digits=6, decimal_places=2)
    
    Days = models.ManyToManyField('HomeAutomation.inlineDaily',blank=True)
        
    def get_formset(self):
        from django.forms import inlineformset_factory
        MainDeviceVarWeeklyScheduleFormset = inlineformset_factory (MainDeviceVarDailyScheduleModel,MainDeviceVarWeeklyScheduleModel,fk_name)
    
    class Meta:
        verbose_name = _('Main device var weekly schedule')
        verbose_name_plural = _('Main device var weekly schedules') 
        unique_together = (('Label', 'Var'))

@receiver(post_save, sender=MainDeviceVarWeeklyScheduleModel, dispatch_uid="update_MainDeviceVarWeeklyScheduleModel")
def update_MainDeviceVarWeeklyScheduleModel(sender, instance, update_fields,**kwargs):
    timestamp=timezone.now() #para hora con info UTC
    
    if not kwargs['created']:   # an instance has been modified
        logger.info('Se ha modificado la planificacion semanal ' + str(instance.Label))
        text=str(_('The weekly schedule ')) + str(instance.Label) + str(_(' has been modified.'))
        PublishEvent(Severity=0,Text=text)
    else:
        logger.info('Se ha creado la planificacion semanal ' + str(instance.Label))
    
    if instance.Active:
        logger.info('Se ha activado la planificacion semanal ' + str(instance.Label) + ' para la variable ' + str(instance.Var))
        schedules=MainDeviceVarWeeklyScheduleModel.objects.filter(Var=instance.Var)
        for schedule in schedules:
            if schedule.Label!=instance.Label:
                schedule.Active=False
                schedule.save()
        checkHourlySchedules()
    
def checkHourlySchedules():
    logger.info('Checking hourly schedules on process ' + str(os.getpid()))
    schedules=MainDeviceVarWeeklyScheduleModel.objects.all()
    timestamp=datetime.datetime.now()
    #logger.info('Timestamp: ' + str(timestamp))
    weekDay=timestamp.weekday()        
    #logger.info('Weekday: ' + str(weekDay))
    hour=timestamp.hour
    #logger.info('Hour: ' + str(hour))
    for schedule in schedules:
        if schedule.Active:
            #logger.info('Schedule: ' + str(schedule.Label) + ' is active')
            #logger.info('Is active!!!')
            dailySchedules=schedule.inlinedaily_set.all()
            for daily in dailySchedules:
                #logger.info('Daily: ' + str(daily))
                if daily.Day==weekDay:
                    Setpoint=getattr(daily,'Hour'+str(hour))
                    #logger.info('Setpoint Hour'+str(hour)+' = ' + str(Setpoint))
                    if Setpoint==0:
                        Value=schedule.LValue
                    else:
                        Value=schedule.HValue
                    variable=MainDeviceVarModel.objects.get(Label=schedule.Var.Label)
                    #logger.info('Variable.value = ' + str(variable.Value))
                    #logger.info('Value = ' + str(Value))
                    if variable.Value!=Value:
                        variable.Value=Value
                        variable.save()
                    break

class inlineDaily(models.Model):
    WEEKDAYS = (
      (0, _("Monday")),
      (1, _("Tuesday")),
      (2, _("Wednesday")),
      (3, _("Thursday")),
      (4, _("Friday")),
      (5, _("Saturday")),
      (6, _("Sunday")),
    )
    STATE_CHOICES=(
        (0,_('LOW')),
        (1,_('HIGH'))
    )
    Day = models.PositiveSmallIntegerField(choices=WEEKDAYS)
    Weekly = models.ForeignKey(MainDeviceVarWeeklyScheduleModel, on_delete=models.CASCADE)
#     Daily = models.ForeignKey('HomeAutomation.MainDeviceVarDailyScheduleModel', on_delete=models.CASCADE)
    Hour0 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour1 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour2 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour3 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour4 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour5 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour6 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour7 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour8 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour9 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour10 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour11 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour12 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour13 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour14 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour15 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour16 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour17 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour18 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour19 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour20 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour21 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour22 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    Hour23 = models.PositiveSmallIntegerField(choices=STATE_CHOICES,default=0)
    
    def __str__(self):
        return self.get_Day_display()
    
    class Meta:
        unique_together = ('Day', 'Weekly')
        verbose_name = _('Main device var hourly schedule')
        verbose_name_plural = _('Main device var hourly schedules')


class AutomationVariablesModel(models.Model):
    Label = models.CharField(max_length=50)
    Tag = models.CharField(max_length=50)
    Device = models.CharField(max_length=50)
    Table = models.CharField(max_length=50)
    BitPos = models.PositiveSmallIntegerField(null=True,blank=True)
    Sample = models.PositiveSmallIntegerField(default=0)
    
    def __str__(self):
        return self.Label
    
    class Meta:
        unique_together = ('Tag','BitPos','Table')
        verbose_name = _('Automation variable')
        verbose_name_plural = _('Automation variables')

@receiver(post_save, sender=AutomationVariablesModel, dispatch_uid="update_AutomationVariablesModel")
def update_AutomationVariablesModel(sender, instance, update_fields,**kwargs):    
    rules=RuleItem.objects.filter((Q(Var1__Tag=instance.Tag) & Q(Var1__Device=instance.Device)) | (Q(Var2__Tag=instance.Tag) & Q(Var2__Device=instance.Device)))
    if len(rules)>0:
        for rule in rules:
            rule.Rule.execute()        
                
class RuleItem(models.Model):
    PREFIX_CHOICES=(
        ('',_('None')),
        ('not ',_('NOT'))
    )
    OPERATOR_CHOICES=(
        ('==','=='),
        ('>','>'),
        ('>=','>='),
        ('<','<'),
        ('<=','<='),
        ('!=','!='),
    )
    BOOL_OPERATOR_CHOICES=(
        ('&',_('AND')),
        ('|',_('OR')),
    )
    Rule = models.ForeignKey('HomeAutomation.AutomationRuleModel', on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(help_text=_('Order of execution'))
    PreVar1 = models.CharField(choices=PREFIX_CHOICES,default='',max_length=3,blank=True)
    Var1= models.ForeignKey(AutomationVariablesModel,related_name='var1')
    Operator12 = models.CharField(choices=OPERATOR_CHOICES+BOOL_OPERATOR_CHOICES,max_length=2)
    PreVar2 = models.CharField(choices=PREFIX_CHOICES,default='',max_length=3,blank=True)
    Var2= models.ForeignKey(AutomationVariablesModel,related_name='var2',blank=True,null=True)
    Var2Hyst= models.DecimalField(max_digits=6, decimal_places=2,default=0.5)
    IsConstant = models.BooleanField(default = False)
    Constant = models.FloatField(blank=True,null=True)
    Operator3 = models.CharField(choices=BOOL_OPERATOR_CHOICES,max_length=2,blank=True,null=True)
    
    def __str__(self):
        return str(self.Rule) + '.' + str(self.order)
    
    def evaluate(self):
        import Devices.BBDD
        import datetime
        from tzlocal import get_localzone
        
        applicationDBs=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                      configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH) 
        local_tz=get_localzone()
        now = timezone.now()
        evaluable=''
        sql='SELECT timestamp,"'+self.Var1.Tag+'" FROM "'+ self.Var1.Table +'" WHERE "'+self.Var1.Tag +'" not null ORDER BY timestamp DESC LIMIT 1'
        timestamp1,value1=applicationDBs.registersDB.retrieve_from_table(sql=sql,single=True,values=(None,))
        
        timestamp1 = local_tz.localize(timestamp1)
        timestamp1=timestamp1+timestamp1.utcoffset() 
        
        if self.Var1.Sample>0:
            if (now-timestamp1>datetime.timedelta(seconds=1.5*self.Var1.Sample)):
                logger.warning('The rule ' + str(self) + ' was evaluated with data older than expected')
                logger.warning('    The latest timestamp for the variable ' + str(self.Var1) + ' was ' + str(timestamp1))
        
        if self.Var1.BitPos!=None:
            value1=value1 & (1<<self.Var1.BitPos) 
         
        
        if self.Var2!= None:
            sql='SELECT timestamp,"'+self.Var2.Tag+'" FROM "'+ self.Var2.Table +'" WHERE "'+self.Var2.Tag +'" not null ORDER BY timestamp DESC LIMIT 1'
            timestamp2,value2=applicationDBs.registersDB.retrieve_from_table(sql=sql,single=True,values=(None,))
            timestamp2 = local_tz.localize(timestamp2)
            timestamp2=timestamp2+timestamp2.utcoffset()
            if self.Var2.Sample>0:
                if (now-timestamp2>datetime.timedelta(seconds=1.5*self.Var2.Sample)):
                    logger.warning('The rule ' + self.Identifier + ' was evaluated with data older than expected')
                    logger.warning('    The latest timestamp for the variable ' + str(self.Var2) + ' was ' + str(timestamp2))
            
            if self.Var2.BitPos!=None:
                value2=value2 & (1<<self.Var2.BitPos)
        else:
            value2=self.Constant
                
        if self.Operator12.find('>')>=0:
            histeresis='+' + str(self.Var2Hyst)
        elif self.Operator12.find('<')>=0:
            histeresis='-' + str(self.Var2Hyst)
        else:
            histeresis=''
        
        evaluable+='('+ self.PreVar1 +' '+str(value1) + ' ' + self.Operator12 + ' ' + self.PreVar2 + str(value2) + histeresis + ')'
        
        return eval(evaluable)
            
    class Meta:
        unique_together=(('Rule','order'))
        verbose_name = _('Automation expression')
        verbose_name_plural = _('Automation expressions')
                
class AutomationRuleModel(models.Model):
    
    
    Identifier = models.CharField(max_length=50,unique=True)
    Active = models.BooleanField(default=False)
    RuleItems = models.ManyToManyField(RuleItem)
    Action = models.CharField(max_length=500,blank=True) # receives a json object describind the action desired
    
    _timestamp1=None
    _timestamp2=None
    
    def __str__(self):
        return self.Identifier
        
    def evaluate(self):
        if self.Active:
            evaluable=''
            RuleItems=RuleItem.objects.filter(Rule=self.pk).order_by('order')
            if len(RuleItems):
                for item in RuleItems:
                    if item.Operator3!=None:
                        evaluable+=' ' + str(item.evaluate()) + ' ' + item.Operator3
                    else:
                        evaluable+=' ' + str(item.evaluate())
                
                return eval(evaluable)
            else:
                return None
        else:
            return None
    
    def execute(self):
        result=self.evaluate()
        if result==True:
            Action=json.loads(self.Action)
            if Action['IO']!=None:
                IO=Master_GPIOs.models.IOmodel.objects.get(pk=Action['IO'])
                IO.value=Action['IOValue']
                IO.save(update_fields=['value'])
            #logger.info('The rule ' + self.Identifier + ' evaluated to True. Action executed.')
            PublishEvent(Severity=0,Text=str(_('The rule '))+self.Identifier+str(_(' evaluated to True. Action executed.')))
        
    class Meta:
        verbose_name = _('Automation rule')
        verbose_name_plural = _('Automation rules')
        
@receiver(post_save, sender=AutomationRuleModel, dispatch_uid="update_AutomationRuleModel")
def update_AutomationRuleModel(sender, instance, update_fields,**kwargs):    
    if not kwargs['created']:   # an instance has been modified
        logger.info('Se ha modificado la regla de automatizacion ' + str(instance.Identifier))
    else:
        logger.info('Se ha creado la regla de automatizacion ' + str(instance.Identifier))