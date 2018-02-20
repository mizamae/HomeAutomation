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
    
    Subsystem = GenericRelation(Subsystems,related_query_name='automationvariables')
    
    def __str__(self):
        return self.Label
    
    def store2DB(self):
        self.full_clean()
        super().save() 
    
    def toggle(self):
        MainAPP.signals.SignalToggleAVAR.send(sender=None,Tag=self.Tag,Device=self.Device)
        
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
        return Data
        
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
                
class RuleItems(models.Model):
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
        if operator=='&':
            return '|'
        elif operator=='|':
            return '&'
        else:
            return operator
    
    def setLastEval(self,value):
        self.LastEval=value
        self.save()
        
    def evaluate(self):
        if self.Active:
            evaluableTRUE=''
            evaluableFALSE=''
            if self.PreviousRule!=None:
                result=self.PreviousRule.evaluate()
                evaluableTRUE+=str(result['TRUE']) + ' ' + self.OperatorPrev
                evaluableFALSE+=str(result['FALSE']) + ' ' + self.switchBOOLOperator(operator=self.OperatorPrev)
            Items=RuleItems.objects.filter(Rule=self.pk).order_by('Order')
            if len(Items):
                errors=[]
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
                        PublishEvent(Severity=3,Text=text,Persistent=True)
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
            PublishEvent(Severity=0,Text=text)
            self.setLastEval(value=True)
        elif resultFALSE==True:
            Action=json.loads(self.Action)
            if Action['IO']!=None and Action['ActionType']=='a':
                MainAPP.signals.SignalSetGPIO.send(sender=None,pk=Action['IO'],Value=int(not int(Action['IOValue'])))
            text='The rule ' + self.Identifier + ' evaluated to False. Action executed.'
            PublishEvent(Severity=0,Text=text)
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
        logger.info('Se ha modificado la regla de automatizacion ' + str(instance.Identifier))
    else:
        logger.info('Se ha creado la regla de automatizacion ' + str(instance.Identifier))
    #if instance.Active==False:
    #    instance.execute(error=True)
        
