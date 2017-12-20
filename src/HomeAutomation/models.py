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
        ('area',_('Area')),
    )
    Label = models.CharField(max_length=50,unique=True)
    Value = models.DecimalField(max_digits=6, decimal_places=2,null=True)
    Datatype=models.PositiveSmallIntegerField(choices=DATATYPE_CHOICES,default=0)
    PlotType= models.CharField(max_length=10,choices=PLOTTYPE_CHOICES,default='line')
    Units = models.CharField(max_length=10)
    UserEditable = models.BooleanField(default=True)
    
    __previous_value = None
    
    def __str__(self):
        return self.Label
    
    def __init__(self, *args, **kwargs):
        super(MainDeviceVarModel, self).__init__(*args, **kwargs)
        self.__previous_value = self.Value
        
    def update_value(self,newValue,timestamp=None,writeDB=True):
        if writeDB:
            registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                            configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')
            if timestamp==None:
                now=timezone.now()
                registerDB.insert_VARs_register(TimeStamp=now-datetime.timedelta(seconds=1),VARs=self)
            else:
                registerDB.insert_VARs_register(TimeStamp=timestamp,VARs=self)
                
        self.Value=newValue
        self.save(update_fields=['Value'])
        
        if writeDB and timestamp==None:
            registerDB.insert_VARs_register(TimeStamp=now,VARs=self)
        
        self.updateAutomationVars()
        
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
def update_MainDeviceVarModel(sender, instance, update_fields=[],**kwargs):
    
    registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                           configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')
    
    if not kwargs['created']:   # an instance has been modified
        #logger.info('Se ha modificado la variable local ' + str(instance) + ' al valor ' + str(instance.Value))
        PublishEvent(Severity=0,Text=str(_('Variable '))+instance.Label+str(_(' has changed. Current value is '))+str(instance.Value) + str(instance.Units))
    else:
        logger.info('Se ha creado la variable local ' + str(instance))
        registerDB.check_IOsTables()
    timestamp=timezone.now() #para hora con info UTC
    #registerDB.insert_VARs_register(TimeStamp=timestamp,VARs=instance)
    

class AdditionalCalculationsModel(models.Model):
    PERIODICITY_CHOICES=(
        (0,_('With every new value')),
        (1,_('Every hour')),
        (2,_('Every day')),
        (3,_('Every week')),
        (4,_('Every month'))
    )
    
    CALCULATION_CHOICES=(
        (0,_('Duty cycle OFF')),
        (1,_('Duty cycle ON')),
        (2,_('Mean value')),
        (3,_('Max value')),
        (4,_('Min value')),
        (5,_('Cummulative sum')),
    )
    
    MainVar = models.OneToOneField(MainDeviceVarModel,on_delete=models.CASCADE,related_name='mvar',blank=True,null=True) # variable that will hold the result of the calculation
    AutomationVar= models.ForeignKey('HomeAutomation.AutomationVariablesModel',on_delete=models.CASCADE,related_name='avar') # variable whose change triggers the calculation
    Periodicity= models.PositiveSmallIntegerField(help_text=_('How often the calculation will be updated'),choices=PERIODICITY_CHOICES)
    Calculation= models.PositiveSmallIntegerField(choices=CALCULATION_CHOICES)
    
    def __str__(self):
        try:
            return str(self.get_Calculation_display())+'('+self.AutomationVar.Label + ')'
        except:
            return ''
    
    def checkTrigger(self):
        if self.Periodicity==0:
            return True
        else:
            import datetime
            now=datetime.datetime.now()
            if self.Periodicity==1 and now.minute==0: # hourly calculation launched at minute XX:00
                return True
            elif now.hour==0 and now.minute==0:
                if self.Periodicity==2: # daily calculation launched on next day at 00:00
                    return True
                elif self.Periodicity==3 and now.weekday()==0: # weekly calculation launched on Monday at 00:00
                    return True
                elif self.Periodicity==4 and now.day==1: # monthly calculation launched on 1st day at 00:00
                    return True
        return False
    
    def calculate(self):
        import datetime
        import calendar
        if self.Periodicity==1: # Every hour
            offset=datetime.timedelta(hours=1)
        elif self.Periodicity==2: # Every day
            offset=datetime.timedelta(hours=24)
        elif self.Periodicity==3: # Every week
            offset=datetime.timedelta(weeks=1)
        elif self.Periodicity==4: # Every month
            now=datetime.datetime.now()
            days=calendar.monthrange(now.year, now.month)[1]
            offset=datetime.timedelta(hours=days*24)
        else:
            return
        toDate=timezone.now() 
        fromDate=toDate-offset
        DBDate=toDate-offset/2
        toDate=toDate-datetime.timedelta(minutes=1)
        data_rows=self.AutomationVar.getValues(fromDate=fromDate,toDate=toDate,localized=False)
        if data_rows!=[]:
            self.df=pd.DataFrame.from_records(data=data_rows,columns=['timestamp',str(self)])
            self.df['weekday'] = self.df['timestamp'].dt.weekday_name
            
            if self.Calculation==0:     # Duty cycle OFF
                result= self.duty(level=False)
            if self.Calculation==1:     # Duty cycle ON
                result= self.duty(level=True)
            elif self.Calculation==2:   # Mean value
                result=self.df.mean()[0]
            elif self.Calculation==3:   # Max value
                result= self.df.max()[0]
            elif self.Calculation==4:   # Min value
                result= self.df.min()[0]
            elif self.Calculation==5:   # Cummulative sum
                result= self.df.cumsum()[0]
            elif self.Calculation==6:
                result= None
            
            if result!=None:
                self.MainVar.update_value(newValue=result,timestamp=DBDate,writeDB=True)
        else:
            text='No registers found to calculate ' + str(self)
            PublishEvent(Severity=3,Text=text,Persistent=True)

    def duty(self,level=False):
        totalTime=self.df['timestamp'].iloc[-1]-self.df['timestamp'].iloc[0]
        totalTime=totalTime.days*86400+totalTime.seconds
        time=0
        previousDate=self.df['timestamp'].iloc[0]
        for index, row in self.df.iterrows():
            date=row['timestamp']
            sampletime=date-previousDate
            time+=int(row[str(self)]==level)*(sampletime.days*86400+sampletime.seconds)
            previousDate=date
        return time/totalTime*100


@receiver(post_save, sender=AdditionalCalculationsModel, dispatch_uid="update_AdditionalCalculationsModel")
def update_AdditionalCalculationsModel(sender, instance, update_fields,**kwargs):
    if kwargs['created']:   # an instance has been created
        logger.info('Se ha creado el calculo ' + str(instance))
        label= str(instance)
        try:
            mainVar=MainDeviceVarModel.objects.get(Label=label)
        except:
            if instance.Calculation>1: # it is not a duty calculation
                mainVar=MainDeviceVarModel(Label=label,Value=0,Datatype=0,Units=instance.AutomationVar.Label.split('_')[-1],UserEditable=False)
            else:
                mainVar=MainDeviceVarModel(Label=label,Value=0,Datatype=0,Units='%',UserEditable=False)
            mainVar.save()
        instance.MainVar=mainVar
        instance.save()

class MainDeviceVarWeeklyScheduleModel(models.Model):
    Label = models.CharField(max_length=50,unique=True)
    Active = models.BooleanField(default=False)
    Var = models.ForeignKey(MainDeviceVarModel,on_delete=models.CASCADE)
    LValue = models.DecimalField(max_digits=6, decimal_places=2)
    HValue = models.DecimalField(max_digits=6, decimal_places=2)
    
    Days = models.ManyToManyField('HomeAutomation.inlineDaily',blank=True)
    
    def set_Active(self,value=True):
        self.Active=value
        self.save()
        
        if self.Active:
            logger.info('Se ha activado la planificacion semanal ' + str(self.Label) + ' para la variable ' + str(self.Var))
            schedules=MainDeviceVarWeeklyScheduleModel.objects.filter(Var=self.Var)
            for schedule in schedules:
                if schedule.Label!=self.Label:
                    schedule.set_Active(value=False)
            checkHourlySchedules()
        
    def get_today_pattern(self):
        timestamp=datetime.datetime.now()
        weekDay=timestamp.weekday()
        hour=timestamp.hour
        dailySchedules=self.inlinedaily_set.all()
        pattern=[]
        for daily in dailySchedules:
            if daily.Day==weekDay:
                for i in range(0,24):
                    Setpoint=getattr(daily,'Hour'+str(i))
                    pattern.append(Setpoint)
                return pattern
        return None
        
    def modify_schedule(self,value,sense='+'):
        import decimal
        if value=='LValue':
            if sense=='-':
                self.LValue-=decimal.Decimal.from_float(0.5)
            else:
                self.LValue+=decimal.Decimal.from_float(0.5)
            self.save()
        elif value=='HValue':
            if sense=='-':
                self.HValue-=decimal.Decimal.from_float(0.5)
            else:
                self.HValue+=decimal.Decimal.from_float(0.5)
            self.save()
        elif value=='REFValue':
            if self.Var.Value==self.HValue:
                Value=self.LValue
            else:
                Value=self.HValue
            self.Var.update_value(newValue=Value,writeDB=True)
        #checkHourlySchedules()
            
    def get_formset(self):
        from django.forms import inlineformset_factory
        MainDeviceVarWeeklyScheduleFormset = inlineformset_factory (MainDeviceVarDailyScheduleModel,MainDeviceVarWeeklyScheduleModel,fk_name)
    
    class Meta:
        verbose_name = _('Main device var weekly schedule')
        verbose_name_plural = _('Main device var weekly schedules') 
        unique_together = (('Label', 'Var'))
        permissions = (
            ("view_schedules", "Can see available automation schedules"),
            ("activate_schedule", "Can change the state of the schedules"),
            ("edit_schedule", "Can create and edit a schedule")
        )

@receiver(post_save, sender=MainDeviceVarWeeklyScheduleModel, dispatch_uid="update_MainDeviceVarWeeklyScheduleModel")
def update_MainDeviceVarWeeklyScheduleModel(sender, instance, update_fields,**kwargs):
    timestamp=timezone.now() #para hora con info UTC
    
    if not kwargs['created']:   # an instance has been modified
        # logger.info('Se ha modificado la planificacion semanal ' + str(instance.Label))
        # text=str(_('The weekly schedule ')) + str(instance.Label) + str(_(' has been modified.'))
        # PublishEvent(Severity=0,Text=text)
        pass
    else:
        logger.info('Se ha creado la planificacion semanal ' + str(instance.Label))
    
    
    
def checkHourlySchedules(init=False):
    #logger.info('Checking hourly schedules on process ' + str(os.getpid()))
    schedules=MainDeviceVarWeeklyScheduleModel.objects.filter(Active=True)
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
                    #logger.info('Variable.value = ' + str(variable.Value))
                    #logger.info('Value = ' + str(Value))
                    if schedule.Var.Value!=Value or init:
                        schedule.Var.update_value(newValue=Value,writeDB=True)
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
    
    def getValue(self,localized=True):
        applicationDBs=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                      configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH) 
        sql='SELECT timestamp,"'+self.Tag+'" FROM "'+ self.Table +'" WHERE "'+self.Tag +'" not null ORDER BY timestamp DESC LIMIT 1'
        timestamp,value=applicationDBs.registersDB.retrieve_from_table(sql=sql,single=True,values=(None,))
        if localized:
            from tzlocal import get_localzone
            local_tz=get_localzone()
            timestamp = local_tz.localize(timestamp)
            timestamp=timestamp+timestamp.utcoffset() 
        return timestamp,value
        
    def getValues(self,fromDate,toDate,localized=True):
        applicationDBs=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                      configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH) 
        sql='SELECT timestamp,"'+self.Tag+'" FROM "'+ self.Table +'" WHERE timestamp BETWEEN "' + str(fromDate).split('+')[0]+'" AND "'+str(toDate).split('+')[0] + '" ORDER BY timestamp ASC'
        data_rows=applicationDBs.registersDB.retrieve_from_table(sql=sql,single=False,values=(None,))
        if localized and len(data_rows)>0:
            from tzlocal import get_localzone
            local_tz=get_localzone()
            for row in data_rows:
                row=list(row)
                row[0] = local_tz.localize(row[0])
                row[0]=row[0]+row[0].utcoffset() 
        
        return data_rows
        
    class Meta:
        unique_together = ('Tag','BitPos','Table')
        verbose_name = _('Automation variable')
        verbose_name_plural = _('Automation variables')

@receiver(post_save, sender=AutomationVariablesModel, dispatch_uid="update_AutomationVariablesModel")
def update_AutomationVariablesModel(sender, instance, update_fields,**kwargs):    
    rules=RuleItem.objects.filter((Q(Var1__Tag=instance.Tag) & Q(Var1__Device=instance.Device)) | (Q(Var2__Tag=instance.Tag) & Q(Var2__Device=instance.Device)))
    if len(rules)>0:
        for rule in rules:
            if not '"ActionType": "z"' in rule.Rule.Action:
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
        import datetime
        
        now = timezone.now()
        evaluableTRUE=''
        evaluableFALSE=''
        timestamp1,value1=self.Var1.getValue(localized=True)
        
        if self.Var1.Sample>0:
            if (now-timestamp1>datetime.timedelta(seconds=2.5*self.Var1.Sample)):
                logger.warning('The rule ' + str(self) + ' was evaluated with data older than expected')
                logger.warning('    The latest timestamp for the variable ' + str(self.Var1) + ' is ' + str(timestamp1))
                return {'TRUE':eval(self.Rule.get_OnError_display()),'FALSE':eval('not ' + self.Rule.get_OnError_display()),'ERROR':'Too old data from var ' + str(self.Var1)}
        
        if self.Var1.BitPos!=None:
            value1=value1 & (1<<self.Var1.BitPos) 
         
        
        if self.Var2!= None:
            timestamp2,value2=self.Var2.getValue(localized=True)
            if self.Var2.Sample>0:
                if (now-timestamp2>datetime.timedelta(seconds=2.5*self.Var2.Sample)):
                    logger.warning('The rule ' + self.Identifier + ' was evaluated with data older than expected')
                    logger.warning('    The latest timestamp for the variable ' + str(self.Var2) + ' is ' + str(timestamp2))
                    return {'TRUE':eval(self.Rule.get_OnError_display()),'FALSE':eval('not ' + self.Rule.get_OnError_display()),'ERROR':'Too old data from var ' + str(self.Var2)}
                    
            if self.Var2.BitPos!=None:
                value2=value2 & (1<<self.Var2.BitPos)
        else:
            value2=self.Constant
                
        if self.Operator12.find('>')>=0:
            histeresisTRUE='+' + str(self.Var2Hyst)
            histeresisFALSE='-' + str(self.Var2Hyst)
        elif self.Operator12.find('<')>=0:
            histeresisTRUE='-' + str(self.Var2Hyst)
            histeresisFALSE='+' + str(self.Var2Hyst)
        else:
            histeresisTRUE=''
            histeresisFALSE=''
        
        evaluableTRUE+='('+ self.PreVar1 +' '+str(value1) + ' ' + self.Operator12 + ' ' + self.PreVar2 + str(value2) + histeresisTRUE + ')'
        evaluableFALSE+='not ('+ self.PreVar1 +' '+str(value1) + ' ' + self.Operator12 + ' ' + self.PreVar2 + str(value2) + histeresisFALSE + ')'
        
        try:
            return {'TRUE':eval(evaluableTRUE),'FALSE':eval(evaluableFALSE)}
        except:
            return {'TRUE':eval(self.Rule.get_OnError_display()),'FALSE':eval('not ' + self.Rule.get_OnError_display()),'ERROR':'Unknown'}
            
    class Meta:
        verbose_name = _('Automation expression')
        verbose_name_plural = _('Automation expressions')
                
class AutomationRuleModel(models.Model):
    BOOL_OPERATOR_CHOICES=(
        ('&',_('AND')),
        ('|',_('OR')),
    )
    ONERROR_CHOICES=(
        (0,_('False')),
        (1,_('True')),
    )
    Identifier = models.CharField(max_length=50,unique=True)
    Active = models.BooleanField(default=False)
    OnError = models.PositiveSmallIntegerField(choices=ONERROR_CHOICES,default=0)
    PreviousRule= models.ForeignKey('AutomationRuleModel',related_name='previous_rule',blank=True,null=True)
    OperatorPrev = models.CharField(choices=BOOL_OPERATOR_CHOICES,max_length=2,blank=True,null=True)
    RuleItems = models.ManyToManyField(RuleItem)
    Action = models.CharField(max_length=500,blank=True) # receives a json object describind the action desired
    
    _timestamp1=None
    _timestamp2=None
    
    def __str__(self):
        return self.Identifier
    
    def printEvaluation(self):
        result=self.evaluate()
        if result['ERROR']==[]:
            result.pop('ERROR', None)
        return str(result)
        
    def switchBOOLOperator(self,operator):
        if operator=='&':
            return '|'
        elif operator=='|':
            return '&'
        else:
            return None
            
    def evaluate(self):
        if self.Active:
            evaluableTRUE=''
            evaluableFALSE=''
            if self.PreviousRule!=None:
                result=self.PreviousRule.evaluate()
                evaluableTRUE+=str(result['TRUE']) + ' ' + self.OperatorPrev
                evaluableFALSE+=str(result['FALSE']) + ' ' + self.switchBOOLOperator(operator=self.OperatorPrev)
            RuleItems=RuleItem.objects.filter(Rule=self.pk).order_by('order')
            if len(RuleItems):
                errors=[]
                for item in RuleItems:
                    result=item.evaluate()
                    resultTRUE=result['TRUE']
                    resultFALSE=result['FALSE']
                    if item.Operator3!=None:
                        evaluableTRUE+=' ' + str(resultTRUE) + ' ' + item.Operator3
                        evaluableFALSE+=' ' + str(resultFALSE) + ' ' + self.switchBOOLOperator(operator=item.Operator3)
                    else:
                        evaluableTRUE+=' ' + str(resultTRUE)
                        evaluableFALSE+=' ' + str(resultFALSE)
                            
                    if 'ERROR' in result:
                        text='The evaluation of rule ' + self.Identifier + ' evaluated to Error on item ' + str(item)+'. Error: ' + str(result['ERROR'])
                        PublishEvent(Severity=0,Text=text,Persistent=True)
                        errors.append(result['ERROR'])
                
                evaluableTRUE=evaluableTRUE.strip()
                evaluableFALSE=evaluableFALSE.strip()
                if len(evaluableTRUE)>1:
                    if evaluableTRUE[-1]=='&' or evaluableTRUE[-1]=='|':
                        evaluableTRUE=evaluableTRUE[:-1]
                    if evaluableTRUE[0]=='&' or evaluableTRUE[0]=='|':
                        evaluableTRUE=evaluableTRUE[1:]
                if len(evaluableFALSE)>1:
                    if evaluableFALSE[-1]=='&' or evaluableFALSE[-1]=='|':
                        evaluableFALSE=evaluableFALSE[:-1]
                    if evaluableFALSE[0]=='&' or evaluableFALSE[0]=='|':
                        evaluableFALSE=evaluableFALSE[1:]
                try:
                    return {'TRUE':evaluableTRUE,'FALSE':evaluableFALSE,'ERROR':errors}
                except:
                    return {'TRUE':None,'FALSE':None,'ERROR':'Unknown'}
            else:
                return {'TRUE':None,'FALSE':None,'ERROR':'Unknown'}
        else:
            return {'TRUE':'','FALSE':'','ERROR':'Inactive Rule'}
    
    def execute(self,error=None):
        
        if error!=None:
            resultTRUE=eval(self.get_OnError_display())
            resultFALSE=eval('not ' + self.get_OnError_display())
        else:
            result=self.evaluate()
            resultTRUE=result['TRUE']
            resultFALSE=result['FALSE']
            
        try:
            resultTRUE=eval(resultTRUE)
            resultFALSE=eval(resultFALSE)
        except:
            resultTRUE=eval(self.get_OnError_display())
            resultFALSE=eval('not ' + self.get_OnError_display())
            
        if resultTRUE==True:
            Action=json.loads(self.Action)
            if Action['IO']!=None:
                IO=Master_GPIOs.models.IOmodel.objects.get(pk=Action['IO'])
                newValue=int(Action['IOValue'])
                IO.update_value(newValue=newValue,timestamp=None,writeDB=True)
            #logger.info('The rule ' + self.Identifier + ' evaluated to True. Action executed.')
            text='The rule ' + self.Identifier + ' evaluated to True. Action executed.'
            PublishEvent(Severity=0,Text=text)
        elif resultFALSE==True:
            Action=json.loads(self.Action)
            if Action['IO']!=None:
                IO=Master_GPIOs.models.IOmodel.objects.get(pk=Action['IO'])
                newValue=int(not int(Action['IOValue']))
                IO.update_value(newValue=newValue,timestamp=None,writeDB=True)
            #logger.info('The rule ' + self.Identifier + ' evaluated to False. Action executed.')
            text='The rule ' + self.Identifier + ' evaluated to False. Action executed.'
            PublishEvent(Severity=0,Text=text)
            
    class Meta:
        verbose_name = _('Automation rule')
        verbose_name_plural = _('Automation rules')
        permissions = (
            ("view_rules", "Can see available automation rules"),
            ("activate_rules", "Can change the state of the rules"),
            ("edit_rules", "Can create and edit a rule")
        )
        
@receiver(post_save, sender=AutomationRuleModel, dispatch_uid="update_AutomationRuleModel")
def update_AutomationRuleModel(sender, instance, update_fields,**kwargs):    
    if not kwargs['created']:   # an instance has been modified
        logger.info('Se ha modificado la regla de automatizacion ' + str(instance.Identifier))
    else:
        logger.info('Se ha creado la regla de automatizacion ' + str(instance.Identifier))
    if instance.Active==False:
        instance.execute(error=True)
        
def init_Rules():
    RULs=AutomationRuleModel.objects.filter(Active=True)
    if len(RULs)>0:
        for RUL in RULs:
            if not '"ActionType": "z"' in RUL.Action:
                RUL.execute() 