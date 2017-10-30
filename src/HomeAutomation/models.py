from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
import datetime

from django.dispatch import receiver
from django.db.models.signals import pre_save,post_save,post_delete,pre_delete

import Devices.GlobalVars
import Devices.BBDD

import logging
logger = logging.getLogger("project")

registerDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                           configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')
                                           
class MainDeviceVarModel(models.Model):
    Label = models.CharField(max_length=50,primary_key=True)
    Value = models.DecimalField(max_digits=6, decimal_places=2)
    Units = models.CharField(max_length=10)
    
    __original_Value = None
    
    def __str__(self):
        return self.Label
    
    def __init__(self, *args, **kwargs):
        super(MainDeviceVarModel, self).__init__(*args, **kwargs)
        self.__original_Value = self.Value
        
    def save(self, *args, **kwargs):
        if self.Value != self.__original_Value and self.__original_Value != '':
             timestamp=timezone.now() #para hora con info UTC
             registerDB.insert_event(TimeStamp=timestamp,Sender='pre_save',DeviceName=self.Label,EventType=registerDB.EVENT_TYPES['VAR_CHANGE'],value=self.__original_Value)
             logger.info('Se ha modificado la variable local ' + str(self) + ' del valor ' + str(self.__original_Value))
        self.__original_Value = self.Value
        super(MainDeviceVarModel, self).save(*args, **kwargs)
        
    class Meta:
        verbose_name = _('Main device var')
        verbose_name_plural = _('Main device vars')   
        
@receiver(post_save, sender=MainDeviceVarModel, dispatch_uid="update_MainDeviceVarModel")
def update_MainDeviceVarModel(sender, instance, update_fields,**kwargs):
    timestamp=timezone.now() #para hora con info UTC
    
    if not kwargs['created']:   # an instance has been modified
        logger.info('Se ha modificado la variable local ' + str(instance) + ' al valor ' + str(instance.Value))
    else:
        logger.info('Se ha creado la variable local ' + str(instance))
    
    registerDB.insert_event(TimeStamp=timestamp,Sender='post_save',DeviceName=instance.Label,EventType=registerDB.EVENT_TYPES['VAR_CHANGE'],value=instance.Value)

## THE AUTOMATION AND SCHEDULING OF THE VARS SHOULD BE IMPLEMENTED
    
# class MainDeviceVarWeeklyScheduleModel(models.Model):
    # Label = models.CharField(max_length=50)
    # Active = models.BooleanField(default=False)
    # Var = models.ForeignKey(MainDeviceVarModel,on_delete=models.CASCADE)
    # LValue = models.DecimalField(max_digits=6, decimal_places=2)
    # HValue = models.DecimalField(max_digits=6, decimal_places=2)
    
    # Day1 = models.ForeignKey('HomeAutomation.MainDeviceVarDailyScheduleModel',blank=True)
    # Day2 = models.ForeignKey('HomeAutomation.MainDeviceVarDailyScheduleModel',blank=True)
    # Day3 = models.ForeignKey('HomeAutomation.MainDeviceVarDailyScheduleModel',blank=True)
    # Day4 = models.ForeignKey('HomeAutomation.MainDeviceVarDailyScheduleModel',blank=True)
    # Day5 = models.ForeignKey('HomeAutomation.MainDeviceVarDailyScheduleModel',blank=True)
    # Day6 = models.ForeignKey('HomeAutomation.MainDeviceVarDailyScheduleModel',blank=True)
    # Day7 = models.ForeignKey('HomeAutomation.MainDeviceVarDailyScheduleModel',blank=True)
    
    # def get_formset(self):
        # from django.forms import inlineformset_factory
        # MainDeviceVarWeeklyScheduleFormset = inlineformset_factory (MainDeviceVarDailyScheduleModel,MainDeviceVarWeeklyScheduleModel,fk_name)
    
    # class Meta:
        # verbose_name = _('Main device var weekly schedule')
        # verbose_name_plural = _('Main device var weekly schedules') 
        # unique_together = ('Label', 'Var')

# class MainDeviceVarDailyScheduleModel(models.Model):
    # STATE_CHOICES=(
        # (0,_('LOW')),
        # (1,_('HIGH'))
    # )
    # WEEKDAYS = (
      # (1, _("Monday")),
      # (2, _("Tuesday")),
      # (3, _("Wednesday")),
      # (4, _("Thursday")),
      # (5, _("Friday")),
      # (6, _("Saturday")),
      # (7, _("Sunday")),
    # )

    # Day = models.PositiveSmallIntegerField(choices=WEEKDAYS)
    # WeeklySchedule = models.ForeignKey(MainDeviceVarWeeklyScheduleModel, on_delete=models.CASCADE)
    
    # Hour0 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour1 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour2 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour3 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour4 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour5 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour6 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour7 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour8 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour9 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour10 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour11 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour12 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour13 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour14 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour15 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour16 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour17 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour18 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour19 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour20 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour21 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour22 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    # Hour23 = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    
    # class Meta:
        # unique_together = ('Day', 'WeeklySchedule')
        # verbose_name = _('Main device var hourly schedule')
        # verbose_name_plural = _('Main device var hourly schedules')
        
    
# class AutomationRuleModel(models.Model):
    # Identifier = models.CharField(max_length=50,primary_key=True)
    # Expression = models.CharField(max_length=100)
    # FrequencyCheck=models.DurationField(default=datetime.timedelta(minutes=10))   
    
    # def __str__(self):
        # return self.Identifier
    
    # class Meta:
        # verbose_name = _('Automation rule')
        # verbose_name_plural = _('Automation rules')