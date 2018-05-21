from django.db.models import Q
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.utils.functional import lazy
from django.core.cache import cache
import datetime
import sys
import os
import json
from EventsAPP.consumers import PublishEvent

from django.dispatch import receiver
from django.db.models.signals import pre_save,post_save,post_delete,pre_delete
from django.contrib.contenttypes.fields import GenericRelation

from MainAPP.constants import REGISTERS_DB_PATH,SUBSYSTEMS_CHOICES

import MainAPP.signals

import utils.BBDD

import pandas as pd
import numpy as np

import logging

logger = logging.getLogger("project")
                                           

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# settings from https://steelkiwi.com/blog/practical-application-singleton-design-pattern/
class SingletonModel(models.Model):
    class Meta:
        abstract = True
        
    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)
        self.set_cache()
    
    def set_cache(self):
        cache.set(self.__class__.__name__, self)
        
    @classmethod
    def load(cls):
        if cache.get(cls.__name__) is None:
            obj, created = cls.objects.get_or_create(pk=1)
            if not created:
                obj.set_cache()
        return cache.get(cls.__name__)

class SiteSettings(SingletonModel):
    class Meta:
        verbose_name = _('Settings')

    FACILITY_NAME= models.CharField(verbose_name=_('Name of the installation'),max_length=100,default='My house')
    SITE_DNS= models.CharField(verbose_name=_('Name of the domain to access the application'),
                                help_text=_('This is the DNS address that gives access to the application from the internet.'),
                                max_length=100,default='myDIY4dot0House.net')
    
    VERSION_AUTO_DETECT=models.BooleanField(verbose_name=_('Autodetect new software releases'),
                                help_text=_('Automatically checks the repository for new software'),default=True)
    VERSION_AUTO_UPDATE=models.BooleanField(verbose_name=_('Apply automatically new software releases'),
                                help_text=_('Automatically updates to (and applies) the latest software'),default=False)
    
    WIFI_SSID= models.CharField(verbose_name=_('WIFI network identificator'),
                                help_text=_('This is the name of the WiFi network generated to communicate with the slaves'),
                                max_length=50,default='DIY4dot0')
    WIFI_PASSW= models.CharField(verbose_name=_('WIFI network passphrase'),
                                help_text=_('This is the encryption password for the WIFI network'),
                                max_length=50,default='DIY4dot0')
    WIFI_IP= models.GenericIPAddressField(verbose_name=_('IP address for the WIFI network'),
                                help_text=_('This is the IP address for the WiFi network generated to communicate with the slaves'),
                                protocol='IPv4', default='10.10.10.1')
    WIFI_MASK= models.GenericIPAddressField(verbose_name=_('WIFI network mask'),
                                help_text=_('This is the mask of the WiFi network generated to communicate with the slaves'),
                                protocol='IPv4', default='255.255.255.0')
    WIFI_GATE= models.GenericIPAddressField(verbose_name=_('WIFI network gateway'),
                                help_text=_('This is the gateway for the WiFi network generated to communicate with the slaves'),
                                protocol='IPv4', default='10.10.10.1')
    
    ETH_IP= models.GenericIPAddressField(verbose_name=_('IP address for the LAN network'),
                                help_text=_('This is the IP for the LAN network that is providing the internet access.'),
                                protocol='IPv4', default='192.168.0.160')
    ETH_MASK= models.GenericIPAddressField(verbose_name=_('Mask for the LAN network'),
                                help_text=_('This is the mask for the LAN network that is providing the internet access.'),
                                protocol='IPv4', default='255.255.255.0')
    ETH_GATE= models.GenericIPAddressField(verbose_name=_('Gateway of the LAN network'),
                                help_text=_('This is the gateway IP of the LAN network that is providing the internet access.'),
                                protocol='IPv4', default='192.168.0.1')
    
    def store2DB(self):
        self.save()

@receiver(post_save, sender=SiteSettings, dispatch_uid="update_SiteSettings")
def update_SiteSettings(sender, instance, update_fields,**kwargs):
    if not kwargs['created']:   # an instance has been created
        logger.info('Se ha creado el calculo ' + str(instance))
         
    
class Permissions(models.Model):
    class Meta:
        verbose_name = _('Permission')
        verbose_name_plural = _('Permissions') 
        permissions = (
            ("view_heating_subsystem", "Can view the Heating subsystem"),
            ("view_garden_subsystem", "Can view the Garden subsystem"),
            ("view_access_subsystem", "Can view the Access subsystem"),
            ("reset_system", "Can force a reset of the system"),
            ("check_updates", "Can check for updates of the system"),
            ("view_devicesapp", "Can view the devicesAPP"),
            ("view_reportingapp", "Can view the reportingAPP"),
            ("view_subsystemsapp", "Can view the subsystemsAPP"),
            ("view_configurationapp", "Can access to the configurationAPP"),
        )
        
class Subsystems(models.Model):
    class Meta:
        verbose_name = _('Subsystem')
        verbose_name_plural = _('Subsystems') 

    content_type = models.ForeignKey(ContentType)
    object_id = models.CharField(max_length=50)
    content_object = GenericForeignKey('content_type', 'object_id')
    Name = models.PositiveSmallIntegerField(choices=SUBSYSTEMS_CHOICES)

    @staticmethod
    def getName2Display(Name):
        for name in SUBSYSTEMS_CHOICES:
            if name[0]==Name:
                return name[1]
        return None
    
    def __str__(self):
        return self.get_Name_display()
    
class AdditionalCalculations(models.Model):
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
        (6,_('Integral over time')),
    )
      
    SinkVar= models.ForeignKey('MainAPP.AutomationVariables',on_delete=models.CASCADE,related_name='sinkvar',blank=True,null=True) # variable that holds the calculation
    SourceVar= models.ForeignKey('MainAPP.AutomationVariables',on_delete=models.CASCADE,related_name='sourcevar') # variable whose change triggers the calculation
    Periodicity= models.PositiveSmallIntegerField(help_text=_('How often the calculation will be updated'),choices=PERIODICITY_CHOICES)
    Calculation= models.PositiveSmallIntegerField(choices=CALCULATION_CHOICES)
      
    def __init__(self,*args,**kwargs):
        try:
            self.df=kwargs.pop('df')
            self.key=kwargs.pop('key')
        except:
            self.df=pd.DataFrame()
            self.key=''
  
        super(AdditionalCalculations, self).__init__(*args, **kwargs)
      
    def store2DB(self):
        from DevicesAPP.constants import DTYPE_FLOAT
        #import DevicesAPP.models
        label= str(self)
        try:
            sinkVAR=AutomationVariables.objects.get(Label=label)
        except:
            if self.Calculation>1: # it is not a duty calculation
                #VAR=DevicesAPP.models.MainDeviceVars(Label=label,Value=0,DataType=DTYPE_FLOAT,Units=self.SourceVar.Units,UserEditable=False)
                data={'Label':label,'Value':0,'DataType':DTYPE_FLOAT,'Units':self.SourceVar.Units,'UserEditable':False}
            else:
                #VAR=DevicesAPP.models.MainDeviceVars(Label=label,Value=0,DataType=DTYPE_FLOAT,Units='%',UserEditable=False)
                data={'Label':label,'Value':0,'DataType':DTYPE_FLOAT,'Units':'%','UserEditable':False}
            MainAPP.signals.SignalCreateMainDeviceVars.send(sender=None,Data=data)
            #VAR.store2DB()
            sinkVAR=AutomationVariables.objects.get(Label=label)
        self.SinkVar=sinkVAR
        self.save()
         
    def __str__(self):
        try:
            return str(self.get_Calculation_display())+'('+self.SourceVar.Label + ')'
        except:
            return self.key
      
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
        query=self.SourceVar.getQuery(fromDate=fromDate,toDate=toDate)
        self.df=pd.read_sql_query(sql=query['sql'],con=query['conn'],index_col='timestamp')
        if not self.df.empty:
            self.key=self.SourceVar.Tag
            # TO FORCE THAT THE INITIAL ROW CONTAINS THE INITIAL DATE
            addedtime=pd.to_datetime(arg=self.df.index.values[0])-fromDate.replace(tzinfo=None)
            if addedtime>datetime.timedelta(minutes=1):
                ts = pd.to_datetime(fromDate.replace(tzinfo=None))
                new_row = pd.DataFrame([[self.df[self.key].iloc[0]]], columns = [self.key], index=[ts])
                self.df=pd.concat([pd.DataFrame(new_row),self.df], ignore_index=False)
                  
            # TO FORCE THAT THE LAST ROW CONTAINS THE END DATE
            addedtime=toDate.replace(tzinfo=None)-pd.to_datetime(arg=self.df.index.values[-1])
            if addedtime>datetime.timedelta(minutes=1):
                ts = pd.to_datetime(toDate.replace(tzinfo=None))
                new_row = pd.DataFrame([[self.df[self.key].iloc[-1]]], columns = [self.key], index=[ts])
                self.df=pd.concat([self.df,pd.DataFrame(new_row)], ignore_index=False)
              
            # RESAMPLING DATA TO 1 MINUTE RESOLUTION AND INTERPOLATING VALUES
            df_resampled=self.df.resample('1T').mean()
            self.df_interpolated=df_resampled.interpolate(method='zero')
                      
            if self.Calculation==0:     # Duty cycle OFF
                result= self.duty(level=False)
            if self.Calculation==1:     # Duty cycle ON
                result= self.duty(level=True)
            elif self.Calculation==2:   # Mean value
                result= self.df_interpolated.mean()[0]
            elif self.Calculation==3:   # Max value
                result= self.df.max()[0]
            elif self.Calculation==4:   # Min value
                result= self.df.min()[0]
            elif self.Calculation==5:   # Cummulative sum
                result= self.df.cumsum()
            elif self.Calculation==6:   # integral over time
                from scipy import integrate
                result=integrate.trapz(y=self.df_interpolated[self.key], x=self.df_interpolated[self.key].index.astype(np.int64) / 10**9)
        else:
            if self.Calculation<=1:     # Duty cycle OFF,ON
                result=0
            else:
                result= None
        
        if not isinstance(result, pd.DataFrame):
            MainAPP.signals.SignalUpdateValueMainDeviceVars.send(sender=None,Tag=self.SinkVar.Tag,timestamp=DBDate,
                                                                 newValue=result)
        else:
            for index, row in result.iterrows():
                MainAPP.signals.SignalUpdateValueMainDeviceVars.send(sender=None,Tag=self.SinkVar.Tag,timestamp=index.to_pydatetime(),
                                                                 newValue=float(row[0]))
                
        return result
              
    def duty(self,level=False,decimals=2,absoluteValue=False):
        if not self.df.empty:
            totalTime=(self.df.iloc[-1].name-self.df.iloc[0].name)
            totalTime=totalTime.days*86400+totalTime.seconds
            value=next(self.df.iterrows())[1]
            if not isinstance(value[0], list):
                time=0
                islist=False
            else:
                time=[]
                for data in value[0]:
                    time.append(0)
                islist=True
                      
            previousDate=self.df.index.values[0]
            for index, row in self.df.iterrows():
                date=row.name
                sampletime=date-previousDate
                if not islist:
                    time+=int(row[self.key]==level)*(sampletime.days*86400+sampletime.seconds)
                else:
                    for i,data in enumerate(row[self.key]):
                        time[i]+=int(data==level)*(sampletime.days*86400+sampletime.seconds)
                previousDate=date
                      
            if absoluteValue==True:
                return time
            else:
                if not islist:
                    return round(time/totalTime*100,decimals)
                else:
                    return [round(x/totalTime*100,decimals) for x in time]
        else:
            return None
  
@receiver(post_save, sender=AdditionalCalculations, dispatch_uid="update_AdditionalCalculations")
def update_AdditionalCalculations(sender, instance, update_fields,**kwargs):
    if kwargs['created']:   # an instance has been created
        logger.info('Se ha creado el calculo ' + str(instance))
         

class AutomationVariables(models.Model):
    class Meta:
        unique_together = ('Tag','BitPos','Table')
        verbose_name = _('Automation variable')
        verbose_name_plural = _('Automation variables')
        
    Label = models.CharField(max_length=50)
    Tag = models.CharField(max_length=50)
    Device = models.CharField(max_length=50)
    Table = models.CharField(max_length=50)
    BitPos = models.PositiveSmallIntegerField(null=True,blank=True)
    Sample = models.PositiveSmallIntegerField(default=0)
    Units = models.CharField(max_length=10,help_text=str(_('Units of the variable.')),blank=True,null=True)
    UserEditable = models.BooleanField(default=True)
    OverrideTime = models.PositiveSmallIntegerField(default=3600)
    
    Subsystem = GenericRelation(Subsystems,related_query_name='automationvariables')
    
    def __str__(self):
        return self.Label
    
    def store2DB(self):
        self.full_clean()
        super().save() 
    
    def updateValue(self,newValue=None,overrideTime=None,**kwargs):
        if self.UserEditable:
            MainAPP.signals.SignalToggleAVAR.send(sender=None,Tag=self.Tag,Device=self.Device,newValue=newValue,**kwargs)
            if overrideTime!=None:
                AutomationVarWeeklySchedules.override(var=self,value=True,duration=overrideTime)
        
    def checkSubsystem(self,Name):
        SSYTMs=Subsystems.objects.filter(automationvariables=self)
        exist=False
        if SSYTMs.count():
            for SSYTM in SSYTMs:
                if SSYTM.Name==Name:
                    exist=True
                    break
        return exist
        
    def createSubsystem(self,Name):
        if not self.checkSubsystem(Name=Name):
            subsystem=Subsystems(Name=Name,content_object=self)
            subsystem.save()
        
    def getLatestData(self,localized=True):
        Data={}
        name=self.Tag
        Data[name]={}
        table=self.Table
        vars='"timestamp","'+name+'"'
        sql='SELECT '+vars+' FROM "'+ table +'" WHERE "'+name +'" not null ORDER BY timestamp DESC LIMIT 1'
        from utils.BBDD import getRegistersDBInstance
        DB=getRegistersDBInstance()
        row=DB.executeTransaction(SQLstatement=sql)
        if row != []:
            row=row[0]
            timestamp=row[0]
            if self.BitPos!=None:
                from utils.dataMangling import checkBit
                row=checkBit(number=row[1],position=self.BitPos)
            else:
                row=row[1]
        else:
            timestamp=None
            row=None
        if localized and timestamp!=None:
            from tzlocal import get_localzone
            local_tz=get_localzone()
            timestamp = local_tz.localize(timestamp)
            timestamp=timestamp+timestamp.utcoffset() 
        Data[name]['timestamp']=timestamp
        Data[name]['value']=row
        Data[name]['label']=self.Label
        return Data
    
    def getLatestValue(self):
        data=self.getLatestData()
        return data[self.Tag]['value']
    
    def getLatestValueString(self):
        value=self.getLatestValue()
        if value!=None:
            return str(value)
        else:
            return str(5)
         
    def getValues(self,fromDate,toDate,localized=True):
        from utils.BBDD import getRegistersDBInstance
        DB=getRegistersDBInstance()
        sql='SELECT timestamp,"'+self.Tag+'" FROM "'+ self.Table +'" WHERE timestamp BETWEEN "' + str(fromDate).split('+')[0]+'" AND "'+str(toDate).split('+')[0] + '" ORDER BY timestamp ASC'
        data_rows=DB.executeTransaction(SQLstatement=sql)
        if localized and len(data_rows)>0:
            from tzlocal import get_localzone
            local_tz=get_localzone()
            for row in data_rows:
                row=list(row)
                row[0] = local_tz.localize(row[0])
                row[0]=row[0]+row[0].utcoffset() 
        return data_rows
    
    def getQuery(self,fromDate,toDate):
        from utils.BBDD import getRegistersDBInstance
        DB=getRegistersDBInstance()
        sql='SELECT timestamp,"'+self.Tag+'" FROM "'+ self.Table +'" WHERE timestamp BETWEEN "' + str(fromDate).split('+')[0]+'" AND "'+str(toDate).split('+')[0] + '" ORDER BY timestamp ASC'
        return {'conn':DB.getConn(),'sql':sql}
        
    def executeAutomationRules(self):
        rules=RuleItems.objects.filter((Q(Var1=self)) | (Q(Var2=self)))
        if len(rules)>0:
            now=timezone.now()
            for rule in rules:
                if not '"ActionType": "z"' in rule.Rule.Action:
                    rule.Rule.execute()
                    
@receiver(post_save, sender=AutomationVariables, dispatch_uid="update_AutomationVariables")
def update_AutomationVariables(sender, instance, update_fields,**kwargs):   
    pass

class AutomationVarWeeklySchedules(models.Model):
    class Meta:
        verbose_name = _('Automation var weekly schedule')
        verbose_name_plural = _('Automation var weekly schedules') 
        unique_together = (('Label', 'Var'))
        permissions = (
            ("view_AutomationVarWeeklySchedules", "Can see available automation schedules"),
            ("activate_AutomationVarWeeklySchedules", "Can change the state of the schedules"),
        )
        
    Label = models.CharField(max_length=100)
    Active = models.BooleanField(default=False)
    Var = models.ForeignKey('MainAPP.AutomationVariables',on_delete=models.CASCADE,limit_choices_to={'UserEditable': True})
    LValue = models.DecimalField(max_digits=6, decimal_places=2)
    HValue = models.DecimalField(max_digits=6, decimal_places=2)
    Overriden = models.BooleanField(default=False)
    Days = models.ManyToManyField('inlineDaily',blank=True)
 
    Subsystem = GenericRelation(Subsystems,related_query_name='weeklyschedules')
    
    def __str__(self):
        return self.Label
    
    def store2DB(self): 
        self.full_clean() 
        super().save() 
        if self.Active:
            self.checkThis()
            
    def setActive(self,value=True):
        self.Active=value
        self.save()
         
        if self.Active:
            logger.info('Se ha activado la planificacion semanal ' + str(self.Label) + ' para la variable ' + str(self.Var))
            SCHDs=AutomationVarWeeklySchedules.objects.filter(Var=self.Var)
            for SCHD in SCHDs:
                if SCHD.Label!=self.Label:
                    SCHD.setActive(value=False)
            self.checkThis()
         
    def getTodaysPattern(self):
        import datetime
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
         
    def modify(self,value,sense='+'):
        import decimal
        if value=='LValue':
            if sense=='-':
                self.LValue-=decimal.Decimal.from_float(0.5)
            else:
                self.LValue+=decimal.Decimal.from_float(0.5)
            self.save(update_fields=['LValue'])
            self.checkThis()
        elif value=='HValue':
            if sense=='-':
                self.HValue-=decimal.Decimal.from_float(0.5)
            else:
                self.HValue+=decimal.Decimal.from_float(0.5)
            self.save(update_fields=['HValue'])
            self.checkThis()
        elif value=='REFValue':
            if self.Var.getLatestValue()==self.HValue:
                Value=self.LValue
            else:
                Value=self.HValue
            self.Var.updateValue(newValue=float(Value),force=False)
             
    def getFormset(self):
        from django.forms import inlineformset_factory
        AutomationVarWeeklySchedulesFormset = inlineformset_factory (AutomationVarWeeklySchedules,AutomationVarWeeklySchedules,fk_name)
    
    def checkThis(self,init=False):
        timestamp=datetime.datetime.now()
        weekDay=timestamp.weekday()        
        hour=timestamp.hour
        if self.Active and (not self.Overriden):
            dailySchedules=self.inlinedaily_set.all()
            for daily in dailySchedules:
                if daily.Day==weekDay:
                    Setpoint=getattr(daily,'Hour'+str(hour))
                    if Setpoint==0:
                        Value=float(self.LValue)
                    elif Setpoint==1:
                        Value=float(self.HValue)
                    else:
                        text='The schedule ' + self.Label + ' returned a non-understandable setpoint (0=LOW,1=HIGH). It returned ' + str(Setpoint)
                        PublishEvent(Severity=2,Text=text,Persistent=True,Code=self.getEventsCode()+'101')
                        break
                    if self.Var.getLatestValue()!=Value or init:
                        self.Var.updateValue(newValue=Value,writeDB=True,force=init)
                    break
    
    @classmethod
    def override(cls,var,value,duration=3600):
        SCHs=cls.objects.filter(Var=var)
        for SCH in SCHs:
            SCH.Overriden=value
            SCH.save()
            PublishEvent(Severity=3,Text="Schedule " + str(SCH)+" is now overriden at time "+str(datetime.datetime.now()),Persistent=True,Code=str(SCH)+'o')
        if value:
            id='Overriding-'+str(var.pk)
            from utils.asynchronous_tasks import BackgroundTimer
            Timer=BackgroundTimer(interval=duration,threadName=id,callable=cls.overrideTimeout,kwargs={'var':var})

    @classmethod
    def overrideTimeout(cls,var):
        SCHs=AutomationVarWeeklySchedules.objects.filter(Var=var)
        for SCH in SCHs:
            SCH.Overriden=False
            SCH.save()
            try:
                SCHu=cls.objects.get(pk=SCH.pk)    # refreshing the instance
                SCHu.checkThis()
            except:
                e = sys.exc_info()[0]
                PublishEvent(Severity=0,Text="Schedule " + str(SCH)+" failed to be checked. Error: " + str(e),Persistent=True,Code=str(SCH)+'r')
            PublishEvent(Severity=0,Text="Schedule " + str(SCH)+" is now released at time "+str(datetime.datetime.now()),Persistent=True,Code=str(SCH)+'r')
        
    @classmethod
    def initialize(cls):
        schedules=cls.objects.all()
        for schedule in schedules:
            schedule.Overriden=False
            
    @classmethod
    def checkAll(cls,init=False):
        schedules=cls.objects.filter(Active=True)
        for schedule in schedules:
            schedule.checkThis(init=init)


            
@receiver(post_save, sender=AutomationVarWeeklySchedules, dispatch_uid="update_AutomationVarWeeklySchedules")
def update_AutomationVarWeeklySchedules(sender, instance, update_fields,**kwargs):
    timestamp=timezone.now() #para hora con info UTC
    if not kwargs['created']:   # an instance has been modified
        pass
    else:
        logger.info('Se ha creado la planificacion semanal ' + str(instance.Label))


class inlineDaily(models.Model):
    class Meta:
        unique_together = ('Day', 'Weekly')
        verbose_name = _('Automation var hourly schedule')
        verbose_name_plural = _('Automation var hourly schedules')
        
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
    Weekly = models.ForeignKey(AutomationVarWeeklySchedules, on_delete=models.CASCADE)
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
     
    def setInlineHours(self,hours):
        if len(hours)!=24:
            text = "Error in setting an inline. The string passed " +hours + " does not have 24 elements" 
            raise DevicesAppException(text)
        else:
            for i,hour in enumerate(hours):
                if int(hour)>0:
                    setattr(self,'Hour'+str(i),1)
                else:
                    setattr(self,'Hour'+str(i),0)
class Thermostats(models.Model):
    class Meta:
        verbose_name = _('Thermostat')
        verbose_name_plural = _('Thermostats')
     
    RITM = models.OneToOneField('MainAPP.RuleItems',help_text=str(_('The rule item that the thermostat is linked to.')),
                           on_delete=models.CASCADE,related_name='ruleitem2thermostat',unique=True,null=False,blank=False,limit_choices_to={'Var2__UserEditable': True})
    
    def __str__(self):
        return str(self.RITM.Rule) + ' - ' + str(self.RITM.Var1) + ' VS ' + str(self.RITM.Var2)
    
class RuleItems(models.Model):
    PREFIX_CHOICES=(
        ('',''),
        ('not ','NOT'),
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
    Rule = models.ForeignKey('MainAPP.AutomationRules', on_delete=models.CASCADE)
    Order = models.PositiveSmallIntegerField(help_text=_('Order of execution'))
    PreVar1 = models.CharField(choices=PREFIX_CHOICES,default='',max_length=3,blank=True)
    Var1= models.ForeignKey(AutomationVariables,related_name='var1')
    Operator12 = models.CharField(choices=OPERATOR_CHOICES+BOOL_OPERATOR_CHOICES,max_length=2)
    PreVar2 = models.CharField(choices=PREFIX_CHOICES,default='',max_length=3,blank=True)
    Var2= models.ForeignKey(AutomationVariables,related_name='var2',blank=True,null=True)
    Var2Hyst= models.FloatField(default=0.5)
    IsConstant = models.BooleanField(default = False)
    Constant = models.FloatField(blank=True,null=True)
    Operator3 = models.CharField(choices=BOOL_OPERATOR_CHOICES,max_length=2,blank=True,null=True)
    
    def __str__(self):
        return str(self.Rule) + '.' + str(self.Order)
    
    def store2DB(self):
        self.full_clean()
        super().save()
        
    def evaluate(self):
        import datetime
        from utils.dataMangling import checkBit
        now = timezone.now()
        evaluableTRUE=''
        evaluableFALSE=''
        data=self.Var1.getLatestData(localized=True)[self.Var1.Tag]
        timestamp1=data['timestamp']
        value1=data['value']
        
        if self.Var1.Sample>0:
            if value1==None or (now-timestamp1>datetime.timedelta(seconds=int(2.5*self.Var1.Sample))):
                logger.warning('The rule ' + self.Rule.Identifier + ' was evaluated with data older than expected')
                logger.warning('    The latest timestamp for the variable ' + str(self.Var1) + ' is ' + str(timestamp1))
                return {'TRUE':eval(str(self.Rule.OnError)),'FALSE':eval('not ' + str(self.Rule.OnError)),'ERROR':'Too old data from var ' + str(self.Var1)}
        
        if self.Var1.BitPos!=None:
            value1=checkBit(number=int(value1),position=self.Var1.BitPos)
         
        if self.Var2!= None:
            data=self.Var2.getLatestData(localized=True)[self.Var2.Tag]
            timestamp2=data['timestamp']
            value2=data['value']
            if self.Var2.Sample>0:
                if value2==None or (now-timestamp2>datetime.timedelta(seconds=int(2.5*self.Var2.Sample))):
                    logger.warning('The rule ' + self.Rule.Identifier + ' was evaluated with data older than expected')
                    logger.warning('    The latest timestamp for the variable ' + str(self.Var2) + ' is ' + str(timestamp2))
                    return {'TRUE':eval(str(self.Rule.OnError)),'FALSE':eval('not ' + str(self.Rule.OnError)),'ERROR':'Too old data from var ' + str(self.Var2)}
                    
            if self.Var2.BitPos!=None:
                value2=checkBit(number=int(value2),position=self.Var2.BitPos)
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
        
        if self.Operator12.find('&')>=0 or self.Operator12.find('|')>=0:
            value1=int(value1)
            value2=int(value2)
            
        evaluableTRUE+='('+ self.PreVar1 +' '+str(value1) + ' ' + self.Operator12 + ' ' + self.PreVar2 + str(value2) + histeresisTRUE + ')'
        evaluableFALSE+='not ('+ self.PreVar1 +' '+str(value1) + ' ' + self.Operator12 + ' ' + self.PreVar2 + str(value2) + histeresisFALSE + ')'
        
        try:
            return {'TRUE':eval(evaluableTRUE),'FALSE':eval(evaluableFALSE),'ERROR':''}
        except:
            return {'TRUE':eval(str(self.Rule.OnError)),'FALSE':eval('not ' + str(self.Rule.OnError)),'ERROR':'Unknown'}
            
    class Meta:
        verbose_name = _('Automation expression')
        verbose_name_plural = _('Automation expressions')
                
class AutomationRules(models.Model):
    class Meta:
        verbose_name = _('Automation rule')
        verbose_name_plural = _('Automation rules')
        permissions = (
            ("view_rules", "Can see available automation rules"),
            ("activate_rules", "Can change the state of the rules"),
        )
        
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
    PreviousRule= models.ForeignKey('AutomationRules',related_name='previous_rule',blank=True,null=True)
    OperatorPrev = models.CharField(choices=BOOL_OPERATOR_CHOICES,max_length=2,blank=True,null=True)
    RuleItems = models.ManyToManyField(RuleItems)
    Action = models.CharField(max_length=500,blank=True) # receives a json object describind the action desired
    LastEval = models.BooleanField(default=False)
    
    _timestamp1=None
    _timestamp2=None
    
    def __str__(self):
        return self.Identifier
    
    def setActive(self,value):
        if value:
            self.Active=True
        else:
            self.Active=False
        self.save()
        
    def store2DB(self):
        self.full_clean()
        super().save()
        
    def printEvaluation(self):
        result=self.evaluate()
        if result['ERROR']==[]:
            result.pop('ERROR', None)
        return result
        
    def switchBOOLOperator(self,operator):
        if '&' in operator:
            return operator.replace('&','|')
        elif '|' in operator:
            return operator.replace('|','&')
        else:
            return operator
    
    def setLastEval(self,value):
        self.LastEval=value
        self.save()
    
    def getEventsCode(self):
        return 'ARULE'+str(self.pk)
        
    def evaluate(self):
        if self.Active:
            evaluableTRUE=''
            evaluableFALSE=''
            if self.PreviousRule!=None:
                result=self.PreviousRule.evaluate()
                evaluableTRUE+=str(result['TRUE']) + ' ' + self.OperatorPrev
                evaluableFALSE+=str(result['FALSE']) + ' ' + self.switchBOOLOperator(operator=self.OperatorPrev)
                errors=[result['ERROR']]
            else:
                errors=[]
            Items=RuleItems.objects.filter(Rule=self.pk).order_by('Order')
                
            if len(Items):
                
                for item in Items:
                    result=item.evaluate()
                    resultTRUE=result['TRUE']
                    resultFALSE=result['FALSE']
                    if item.Operator3!=None:
                        evaluableTRUE+=' ' + str(resultTRUE) + ' ' + item.Operator3
                        evaluableFALSE+=' ' + str(resultFALSE) + ' ' + self.switchBOOLOperator(operator=item.Operator3)
                    else:
                        evaluableTRUE+=' ' + str(resultTRUE)
                        evaluableFALSE+=' ' + str(resultFALSE)
                            
                    if result['ERROR']!='':
                        text='The evaluation of rule ' + self.Identifier + ' evaluated to Error on item ' + str(item)+'. Error: ' + str(result['ERROR'])
                        PublishEvent(Severity=3,Text=text,Persistent=True,Code=self.getEventsCode())
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
                    return {'TRUE':evaluableTRUE.strip(),'FALSE':evaluableFALSE.strip(),'ERROR':errors}
                except:
                    return {'TRUE':None,'FALSE':None,'ERROR':'Unknown'}
            else:
                return {'TRUE':'','FALSE':'','ERROR':'The rule has no items associated. Cannot be evaluated'}
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
            if Action['IO']!=None and Action['ActionType']=='a':
                MainAPP.signals.SignalSetGPIO.send(sender=None,pk=Action['IO'],Value=int(Action['IOValue']))
            text='The rule ' + self.Identifier + ' evaluated to True. Action executed.'
            if result['ERROR']==[]:
                PublishEvent(Severity=0,Text=text,Persistent=True,Code=self.getEventsCode())
            self.setLastEval(value=True)
        elif resultFALSE==True:
            Action=json.loads(self.Action)
            if Action['IO']!=None and Action['ActionType']=='a':
                MainAPP.signals.SignalSetGPIO.send(sender=None,pk=Action['IO'],Value=int(not int(Action['IOValue'])))
            text='The rule ' + self.Identifier + ' evaluated to False. Action executed.'
            if result['ERROR']==[]:
                PublishEvent(Severity=0,Text=text,Persistent=True,Code=self.getEventsCode())
            self.setLastEval(value=False)
    
    @classmethod
    def initAll(cls):
        RULs=cls.objects.filter(Active=True)
        if len(RULs)>0:
            for RUL in RULs:
                if not '"ActionType": "z"' in RUL.Action:
                    RUL.execute() 
                
@receiver(post_save, sender=AutomationRules, dispatch_uid="update_AutomationRuleModel")
def update_AutomationRuleModel(sender, instance, update_fields,**kwargs):    
    if not kwargs['created']:   # an instance has been modified
        pass
        #logger.info('Se ha modificado la regla de automatizacion ' + str(instance.Identifier))
    else:
        logger.info('Se ha creado la regla de automatizacion ' + str(instance.Identifier))
    #if instance.Active==False:
    #    instance.execute(error=True)
        
