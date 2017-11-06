from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
import datetime
import sys

from django.dispatch import receiver
from django.db.models.signals import pre_save,post_save,post_delete,pre_delete

import Devices.GlobalVars
import Devices.BBDD

import logging

logger = logging.getLogger("project")

                                           
class MainDeviceVarModel(models.Model):
    DATATYPE_CHOICES=(
        (0,_('Float')),
        (1,_('Integer'))
    )
    
    Label = models.CharField(max_length=50,primary_key=True)
    Value = models.DecimalField(max_digits=6, decimal_places=2)
    Datatype=models.PositiveSmallIntegerField(choices=DATATYPE_CHOICES,default=0)
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
            logger.info('Se ha modificado la variable local ' + str(self) + ' del valor ' + str(self.__original_Value))
        self.__original_Value = self.Value
        super(MainDeviceVarModel, self).save(*args, **kwargs)
        
    class Meta:
        verbose_name = _('Main device var')
        verbose_name_plural = _('Main device vars')   
        
@receiver(post_save, sender=MainDeviceVarModel, dispatch_uid="update_MainDeviceVarModel")
def update_MainDeviceVarModel(sender, instance, update_fields,**kwargs):
    timestamp=timezone.now() #para hora con info UTC
    registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                           configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')
    
    if not kwargs['created']:   # an instance has been modified
        logger.info('Se ha modificado la variable local ' + str(instance) + ' al valor ' + str(instance.Value))
    else:
        logger.info('Se ha creado la variable local ' + str(instance))
        registerDB.check_IOsTables()
    
    registerDB.insert_VARs_register(TimeStamp=timestamp)
    
class MainDeviceVarWeeklyScheduleModel(models.Model):
    Label = models.CharField(max_length=50)
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
    else:
        logger.info('Se ha creado la planificacion semanal ' + str(instance.Label))
    
    if instance.Active:
        logger.info('Se ha activado la planificacion semanal ' + str(instance.Label) + ' para la variable ' + str(instance.Var))
        schedules=MainDeviceVarWeeklyScheduleModel.objects.filter(Var=instance.Var)
        for schedule in schedules:
            if schedule.Var!=instance.Var or schedule.Label!=instance.Label:
                schedule.Active=False
                schedule.save()
        checkHourlySchedules()
    
def checkHourlySchedules():
    logger.info('Checking hourly schedules')
    schedules=MainDeviceVarWeeklyScheduleModel.objects.all()
    timestamp=datetime.datetime.now()
    weekDay=timestamp.weekday()
    hour=timestamp.hour
    for schedule in schedules:
        if schedule.Active:
            dailySchedules=schedule.inlinedaily_set.all()
            for daily in dailySchedules:
                if daily.Day==weekDay:
                    Setpoint=getattr(daily,'Hour'+str(hour))
                    if Setpoint==0:
                        Value=schedule.LValue
                    else:
                        Value=schedule.HValue
                    variable=MainDeviceVarModel.objects.get(Label=schedule.Var.Label)
                    if variable.Value!=Value:
                        variable.Value=Value
                        variable.save()

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
    
class AutomationRuleModel(models.Model):
    Identifier = models.CharField(max_length=50,primary_key=True)
    Expression = models.CharField(max_length=100)
    FrequencyCheck=models.DurationField(default=datetime.timedelta(minutes=10))   
    
    def __str__(self):
        return self.Identifier
    
    class Meta:
        verbose_name = _('Automation rule')
        verbose_name_plural = _('Automation rules')