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

    def __str__(self):
        return self.get_Name_display()
    

# class AdditionalCalculationsModel(models.Model):
#     PERIODICITY_CHOICES=(
#         (0,_('With every new value')),
#         (1,_('Every hour')),
#         (2,_('Every day')),
#         (3,_('Every week')),
#         (4,_('Every month'))
#     )
#     
#     CALCULATION_CHOICES=(
#         (0,_('Duty cycle OFF')),
#         (1,_('Duty cycle ON')),
#         (2,_('Mean value')),
#         (3,_('Max value')),
#         (4,_('Min value')),
#         (5,_('Cummulative sum')),
#         (6,_('Integral over time')),
#     )
#     
#     MainVar = models.OneToOneField(MainDeviceVarModel,on_delete=models.CASCADE,related_name='mvar',blank=True,null=True) # variable that will hold the result of the calculation
#     AutomationVar= models.ForeignKey('HomeAutomation.AutomationVariables',on_delete=models.CASCADE,related_name='avar') # variable whose change triggers the calculation
#     Periodicity= models.PositiveSmallIntegerField(help_text=_('How often the calculation will be updated'),choices=PERIODICITY_CHOICES)
#     Calculation= models.PositiveSmallIntegerField(choices=CALCULATION_CHOICES)
#     
#     def __init__(self,*args,**kwargs):
#         try:
#             self.df=kwargs.pop('df')
#             self.key=kwargs.pop('key')
#         except:
#             self.df=pd.DataFrame()
#             self.key=''
# 
#         super(AdditionalCalculationsModel, self).__init__(*args, **kwargs)
#         
#     def __str__(self):
#         try:
#             return str(self.get_Calculation_display())+'('+self.AutomationVar.Label + ')'
#         except:
#             return self.key
#     
#     def checkTrigger(self):
#         if self.Periodicity==0:
#             return True
#         else:
#             import datetime
#             now=datetime.datetime.now()
#             if self.Periodicity==1 and now.minute==0: # hourly calculation launched at minute XX:00
#                 return True
#             elif now.hour==0 and now.minute==0:
#                 if self.Periodicity==2: # daily calculation launched on next day at 00:00
#                     return True
#                 elif self.Periodicity==3 and now.weekday()==0: # weekly calculation launched on Monday at 00:00
#                     return True
#                 elif self.Periodicity==4 and now.day==1: # monthly calculation launched on 1st day at 00:00
#                     return True
#         return False
#     
#     def calculate(self):
#         import datetime
#         import calendar
#         if self.Periodicity==1: # Every hour
#             offset=datetime.timedelta(hours=1)
#         elif self.Periodicity==2: # Every day
#             offset=datetime.timedelta(hours=24)
#         elif self.Periodicity==3: # Every week
#             offset=datetime.timedelta(weeks=1)
#         elif self.Periodicity==4: # Every month
#             now=datetime.datetime.now()
#             days=calendar.monthrange(now.year, now.month)[1]
#             offset=datetime.timedelta(hours=days*24)
#         else:
#             return
#         toDate=timezone.now() 
#         fromDate=toDate-offset
#         DBDate=toDate-offset/2
#         toDate=toDate-datetime.timedelta(minutes=1)
#         query=self.AutomationVar.getQuery(fromDate=fromDate,toDate=toDate)
#         self.df=pd.read_sql_query(sql=query['sql'],con=query['conn'],index_col='timestamp')
#         if not self.df.empty:
#             self.key=self.AutomationVar.Tag
#             # TO FORCE THAT THE INITIAL ROW CONTAINS THE INITIAL DATE
#             addedtime=pd.to_datetime(arg=self.df.index.values[0])-fromDate.replace(tzinfo=None)
#             if addedtime>datetime.timedelta(minutes=1):
#                 ts = pd.to_datetime(fromDate.replace(tzinfo=None))
#                 new_row = pd.DataFrame([[self.df[self.key].iloc[0]]], columns = [self.key], index=[ts])
#                 self.df=pd.concat([pd.DataFrame(new_row),self.df], ignore_index=False)
#                 
#             # TO FORCE THAT THE LAST ROW CONTAINS THE END DATE
#             addedtime=toDate.replace(tzinfo=None)-pd.to_datetime(arg=self.df.index.values[-1])
#             if addedtime>datetime.timedelta(minutes=1):
#                 ts = pd.to_datetime(toDate.replace(tzinfo=None))
#                 new_row = pd.DataFrame([[self.df[self.key].iloc[-1]]], columns = [self.key], index=[ts])
#                 self.df=pd.concat([self.df,pd.DataFrame(new_row)], ignore_index=False)
#             
#             # RESAMPLING DATA TO 1 MINUTE RESOLUTION AND INTERPOLATING VALUES
#             df_resampled=self.df.resample('1T').mean()
#             self.df_interpolated=df_resampled.interpolate(method='zero')
#                     
#             if self.Calculation==0:     # Duty cycle OFF
#                 result= self.duty(level=False)
#             if self.Calculation==1:     # Duty cycle ON
#                 result= self.duty(level=True)
#             elif self.Calculation==2:   # Mean value
#                 result= self.df_interpolated.mean()[0]
#             elif self.Calculation==3:   # Max value
#                 result= self.df.max()[0]
#             elif self.Calculation==4:   # Min value
#                 result= self.df.min()[0]
#             elif self.Calculation==5:   # Cummulative sum
#                 result= self.df_interpolated.cumsum()[0]
#             elif self.Calculation==6:   # integral over time
#                 from scipy import integrate
#                 result=integrate.trapz(y=self.df_interpolated[self.key], x=self.df_interpolated[self.key].index.astype(np.int64) / 10**9)
#         else:
#             result= None
#             self.MainVar.update_value(newValue=None,timestamp=DBDate,writeDB=True)
#         
#         if result!=None:
#             self.MainVar.update_value(newValue=result,timestamp=DBDate,writeDB=True)
#             
#     def duty(self,level=False,decimals=2,absoluteValue=False):
#         if not self.df.empty:
#             totalTime=(self.df.iloc[-1].name-self.df.iloc[0].name)
#             totalTime=totalTime.days*86400+totalTime.seconds
#             value=next(self.df.iterrows())[1]
#             if not isinstance(value[0], list):
#                 time=0
#                 islist=False
#             else:
#                 time=[]
#                 for data in value[0]:
#                     time.append(0)
#                 islist=True
#                     
#             previousDate=self.df.index.values[0]
#             for index, row in self.df.iterrows():
#                 date=row.name
#                 sampletime=date-previousDate
#                 if not islist:
#                     time+=int(row[self.key]==level)*(sampletime.days*86400+sampletime.seconds)
#                 else:
#                     for i,data in enumerate(row[self.key]):
#                         time[i]+=int(data==level)*(sampletime.days*86400+sampletime.seconds)
#                 previousDate=date
#                     
#             if absoluteValue==True:
#                 return time
#             else:
#                 if not islist:
#                     return round(time/totalTime*100,decimals)
#                 else:
#                     return [round(x/totalTime*100,decimals) for x in time]
#         else:
#             return None
# 
# @receiver(post_save, sender=AdditionalCalculationsModel, dispatch_uid="update_AdditionalCalculationsModel")
# def update_AdditionalCalculationsModel(sender, instance, update_fields,**kwargs):
#     if kwargs['created']:   # an instance has been created
#         logger.info('Se ha creado el calculo ' + str(instance))
#         label= str(instance)
#         try:
#             mainVar=MainDeviceVarModel.objects.get(Label=label)
#         except:
#             if instance.Calculation>1: # it is not a duty calculation
#                 mainVar=MainDeviceVarModel(Label=label,Value=0,Datatype=0,Units=instance.AutomationVar.Label.split('_')[-1],UserEditable=False)
#             else:
#                 mainVar=MainDeviceVarModel(Label=label,Value=0,Datatype=0,Units='%',UserEditable=False)
#             mainVar.save()
#         instance.MainVar=mainVar
#         instance.save()


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
    Subsystem = GenericRelation(Subsystems,related_query_name='automationvariables')
    
    def __str__(self):
        return self.Label
    
    def store2DB(self):
        self.full_clean()
        super().save() 
        
    def create(self,Label,Tag,Device,Table,BitPos,Sample,Units):
        self.Label=Label
        self.Device=Device
        self.Tag=Tag
        self.Table=Table
        self.BitPos=BitPos
        self.Sample=Sample
        self.Units=Units
        self.store2DB()
        
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
        subsystem=Subsystems(Name=Name,content_object=self)
        subsystem.save()
        
    def getLatestData(self,localized=True):
        Data={}
        name=self.Tag
        Data[name]={}
        table=self.Table
        vars='"timestamp","'+name+'"'
        sql='SELECT '+vars+' FROM "'+ table +'" ORDER BY timestamp DESC LIMIT 1'
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
        AppDB=DevicesAPP.BBDD.DIY4dot0_Databases(registerDBPath=REGISTERS_DB_PATH) 
        sql='SELECT timestamp,"'+self.Tag+'" FROM "'+ self.Table +'" WHERE timestamp BETWEEN "' + str(fromDate).split('+')[0]+'" AND "'+str(toDate).split('+')[0] + '" ORDER BY timestamp ASC'
        return {'conn':AppDB.registersDB.conn,'sql':sql}
        
    def executeAutomationRules(self):
        rules=RuleItems.objects.filter((Q(Var1=self)) | (Q(Var2=self)))
        if len(rules)>0:
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
    order = models.PositiveSmallIntegerField(help_text=_('Order of execution'))
    PreVar1 = models.CharField(choices=PREFIX_CHOICES,default='',max_length=3,blank=True)
    Var1= models.ForeignKey(AutomationVariables,related_name='var1')
    Operator12 = models.CharField(choices=OPERATOR_CHOICES+BOOL_OPERATOR_CHOICES,max_length=2)
    PreVar2 = models.CharField(choices=PREFIX_CHOICES,default='',max_length=3,blank=True)
    Var2= models.ForeignKey(AutomationVariables,related_name='var2',blank=True,null=True)
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
                
class AutomationRules(models.Model):
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
            RuleItems=RuleItems.objects.filter(Rule=self.pk).order_by('order')
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
            if Action['IO']!=None and Action['ActionType']=='a':
                IO=Master_GPIOs.models.IOmodel.objects.get(pk=Action['IO'])
                newValue=int(Action['IOValue'])
                IO.update_value(newValue=newValue,timestamp=None,writeDB=True)
            text='The rule ' + self.Identifier + ' evaluated to True. Action executed.'
            PublishEvent(Severity=0,Text=text)
        elif resultFALSE==True:
            Action=json.loads(self.Action)
            if Action['IO']!=None and Action['ActionType']=='a':
                IO=Master_GPIOs.models.IOmodel.objects.get(pk=Action['IO'])
                newValue=int(not int(Action['IOValue']))
                IO.update_value(newValue=newValue,timestamp=None,writeDB=True)
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
        
@receiver(post_save, sender=AutomationRules, dispatch_uid="update_AutomationRuleModel")
def update_AutomationRuleModel(sender, instance, update_fields,**kwargs):    
    if not kwargs['created']:   # an instance has been modified
        logger.info('Se ha modificado la regla de automatizacion ' + str(instance.Identifier))
    else:
        logger.info('Se ha creado la regla de automatizacion ' + str(instance.Identifier))
    if instance.Active==False:
        instance.execute(error=True)
        
def init_Rules():
    RULs=AutomationRules.objects.filter(Active=True)
    if len(RULs)>0:
        for RUL in RULs:
            if not '"ActionType": "z"' in RUL.Action:
                RUL.execute() 