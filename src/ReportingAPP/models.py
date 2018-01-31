import os
import sys
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.db.models.signals import post_save,post_delete,pre_delete
from django.db.models.signals import m2m_changed

from .constants import DAILY_PERIODICITY,WEEKLY_PERIODICITY,MONTHLY_PERIODICITY,PERIODICITY_CHOICES, \
                        NO_AGGREGATION,HOURLY_AGGREGATION,DAILY_AGGREGATION,MONTHLY_AGGREGATION,AGGREGATION_CHOICES


class ReportModelManager(models.Manager):
    def create_Report(self, ReportTitle,Periodicity,DataAggregation,ReportContentJSON):
        Rep = self.create(ReportTitle=ReportTitle,Periodicity=Periodicity,DataAggregation=DataAggregation,ReportContentJSON=ReportContentJSON)
        Rep.save()
        
class ReportModel(models.Model):
    
    ReportTitle = models.CharField(max_length=50,unique=True,error_messages={'unique':_("Invalid report title - This title already exists in the DB.")})
    Periodicity= models.PositiveSmallIntegerField(help_text=_('How often the report will be generated'),choices=PERIODICITY_CHOICES)
    DataAggregation= models.PositiveSmallIntegerField(help_text=_('Data directly from the DB or averaged over a period'),choices=AGGREGATION_CHOICES)
    ReportContentJSON=models.CharField(help_text='Content of the report in JSON format', max_length=20000)
    
    objects = ReportModelManager()
    
    def checkTrigger(self):
        import datetime
        now=datetime.datetime.now()
        if now.hour==0 and now.minute==0:
            if self.Periodicity==DAILY_PERIODICITY: # daily report launched on next day at 00:00
                return True
            elif self.Periodicity==WEEKLY_PERIODICITY and now.weekday()==0: # weekly report launched on Monday at 00:00
                return True
            elif self.Periodicity==MONTHLY_PERIODICITY and now.day==1: # monthly report launched on 1st day at 00:00
                return True
        return False
    
    def getReportData(self,toDate=None):
        from DevicesAPP.Reports import get_report
        import datetime
        if self.Periodicity==DAILY_PERIODICITY: # daily report
            offset=datetime.timedelta(hours=24)
        elif self.Periodicity==WEEKLY_PERIODICITY: # weekly report
            offset=datetime.timedelta(weeks=1)
        elif self.Periodicity==MONTHLY_PERIODICITY: # monthly report
            if toDate==None:
                now=datetime.datetime.now()
            else:
                now=toDate
            days=calendar.monthrange(now.year, now.month)[1]
            offset=datetime.timedelta(hours=days*24)
        if toDate==None:
            toDate=timezone.now() 
        fromDate=toDate-offset
        toDate=toDate-datetime.timedelta(minutes=1)
        reportData=get_report(reporttitle=self.ReportTitle,fromDate=fromDate,toDate=toDate,aggregation=self.DataAggregation)
        return reportData,fromDate,toDate
        #reportData= {'reportTitle': 'Prueba1', 'fromDate': datetime.datetime(2017, 8, 30, 9, 14, 38), 'toDate': datetime.datetime(2017, 8, 31, 2, 0), 
        # 'charts': [{'chart_title': 'Temperatura', 'cols': [{'table': 'Ambiente en salon_data', 'name': 'Temperature_degC', 'label': 'Temperature_degC', 'type': 'number', 'bitPos': None}, {'table': 'Ambiente en salon_data', 'name': 'Heat Index_degC', 'label': 'Heat Index_degC', 'type': 'number', 'bitPos': None}], 'rows': {'x_axis': [{'v': 'Date(2017,7,30,9,30,0)'}, {'v': 'Date(2017,7,30,10,30,0)'}, {'v': 'Date(2017,7,30,11,30,0)'}, {'v': 'Date(2017,7,30,12,30,0)'}, {'v': 'Date(2017,7,30,13,30,0)'}, {'v': 'Date(2017,7,30,14,30,0)'}, {'v': 'Date(2017,7,30,15,30,0)'}, {'v': 'Date(2017,7,30,16,30,0)'}, {'v': 'Date(2017,7,30,17,30,0)'}, {'v': 'Date(2017,7,30,18,30,0)'}, {'v': 'Date(2017,7,30,19,30,0)'}, {'v': 'Date(2017,7,30,20,30,0)'}, {'v': 'Date(2017,7,30,21,30,0)'}, {'v': 'Date(2017,7,30,22,30,0)'}, {'v': 'Date(2017,7,30,23,30,0)'}, {'v': 'Date(2017,7,31,0,30,0)'}, {'v': 'Date(2017,7,31,1,30,0)'}], 'y_axis': [[26.6, 0.0], [26.916666666666664, 0.0], [27.0, 0.0], [27.02777777777778, 0.0], [27.12121212121212, 0.0], [27.44827586206896, 0.0], [28.0, 0.0], [28.0, 0.0], [28.0, 0.0], [28.0, 0.0], [28.0, 0.0], [27.583333333333332, 0.0], [27.138888888888893, 0.0], [27.055555555555557, 0.0], [27.138888888888893, 0.0], [27.0, 0.0], [27.0, 0.0]]}}, 
        #           {'chart_title': 'Humedad', 'cols': [{'table': 'Ambiente en salon_data', 'name': 'RH_pc', 'label': 'RH_pc', 'type': 'number', 'bitPos': None}], 'rows': {'x_axis': [{'v': 'Date(2017,7,30,9,30,0)'}, {'v': 'Date(2017,7,30,10,30,0)'}, {'v': 'Date(2017,7,30,11,30,0)'}, {'v': 'Date(2017,7,30,12,30,0)'}, {'v': 'Date(2017,7,30,13,30,0)'}, {'v': 'Date(2017,7,30,14,30,0)'}, {'v': 'Date(2017,7,30,15,30,0)'}, {'v': 'Date(2017,7,30,16,30,0)'}, {'v': 'Date(2017,7,30,17,30,0)'}, {'v': 'Date(2017,7,30,18,30,0)'}, {'v': 'Date(2017,7,30,19,30,0)'}, {'v': 'Date(2017,7,30,20,30,0)'}, {'v': 'Date(2017,7,30,21,30,0)'}, {'v': 'Date(2017,7,30,22,30,0)'}, {'v': 'Date(2017,7,30,23,30,0)'}, {'v': 'Date(2017,7,31,0,30,0)'}, {'v': 'Date(2017,7,31,1,30,0)'}], 'y_axis': [[29.4], [29.083333333333336], [29.0], [29.027777777777782], [29.0], [29.0], [29.0], [29.0], [29.0], [29.0], [29.0], [29.0], [29.0], [29.0], [29.027777777777782], [29.0], [29.0]]}}]}
    
    def generate(self):
        ReportData,fromDate,toDate=self.getReportData()                   
        RITM=ReportItems(Report=self,fromDate=fromDate,toDate=toDate,data='')
        RITM.save()
        
    def __str__(self):
        return self.ReportTitle
        
    class Meta:
        permissions = (
            ("add_report", "Can configure and add reports"),
            ("view_report", "Can view reports configured"),
            ("view_plots", "Can see the historic plots from any device")
        )
        verbose_name = _('Report')
        verbose_name_plural = _('Reports')

def path_reportfile_name(instance, filename):
    import os
    from django.conf import settings
    filename, file_extension = os.path.splitext(filename)
    return os.path.join(settings.MEDIA_ROOT,'Reports',instance.Report.ReportTitle+'_'+str(instance.fromDate).split('+')[0].split('.')[0]+'-'+str(instance.toDate).split('+')[0].split('.')[0] +file_extension)

class ReportItems(models.Model):
    Report = models.ForeignKey(ReportModel, on_delete=models.CASCADE)
    fromDate = models.DateTimeField(blank = True,editable=False,null=True)
    toDate = models.DateTimeField(blank = True,editable=False,null=True)
    data = models.CharField(help_text='Data of the report in JSON format', max_length=20000,null=True,blank=True)
    
    def __str__(self):
        return str(self.Report.ReportTitle)
        
    class Meta:
        unique_together = ('Report', 'fromDate','toDate')
        verbose_name = _('Generated report')
        verbose_name_plural = _('Generated reports')
        ordering = ('fromDate',)