import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler

import HomeAutomation.models
import Devices.GlobalVars
import Devices.BBDD

from Events.consumers import PublishEvent

logger = logging.getLogger("project")

scheduler = BackgroundScheduler()                    

def compactRegistersDB():
    AppDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                           configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH)
    rows=AppDB.registersDB.retrieve_DB_structure(fields='*')
    import datetime
    now=datetime.datetime.now()
    sizep = os.path.getsize(Devices.GlobalVars.REGISTERS_DB_PATH.replace('_XYEARX_', str(now.year)))
    for row in rows:
        table_name=row[1]
        AppDB.registersDB.compact_table(table=table_name)
    size = os.path.getsize(Devices.GlobalVars.REGISTERS_DB_PATH.replace('_XYEARX_', str(now.year)))
    PublishEvent(Severity=0,Text='The DB size is reduced from ' +str(sizep/1000) + ' to ' + str(size/1000) + ' kB after compactation',Persistent=True)
    
def start_registersDBcompactingTask(): 
    '''COMPACTS THE REGISTER'S TABLE MONTHLY ON THE LAST DAY OF THE MONTH AT 00:00:00
    '''  
    logger.info('Registers DB compacting task is added to scheduler on the process '+ str(os.getpid())) 
    scheduler.add_job(func=compactRegistersDB,trigger='cron',id='registerDBcompact',day='last',hour=0,minute=0,max_instances=1)
    try:
        scheduler.start()
    except:
        pass

def checkReportAvailability():
    '''THIS TASK IS RUN EVERY DAY AT HOUR 0 AND CHECKS IF ANY REPORT TRIGGERING CONDITION IS MET.
    IN CASE SO, IT GENERATES THE REPORT.
    '''
    from Devices.models import ReportModel,ReportItems
    import json
    reports=ReportModel.objects.all()
    for report in reports:
        if report.checkTrigger():
            ReportData,fromDate,toDate=report.getReport()
            reportTitle=report.ReportTitle                     
            report=ReportModel.objects.get(ReportTitle=reportTitle)
            rp=ReportItems(Report=report,fromDate=fromDate,toDate=toDate,data=json.dumps(ReportData))
            rp.save()

def updateWeekDay():
    import datetime
    from HomeAutomation.models import MainDeviceVarModel
    timestamp=datetime.datetime.now()
    weekDay=timestamp.weekday()
    try:
        WeekDay=MainDeviceVarModel.objects.get(Label='Day of the week')
        WeekDay.update_value(newValue=weekDay,writeDB=True)
        #WeekDay.UserEditable=False
    except:
        WeekDay=MainDeviceVarModel(Label='Day of the week',Value=weekDay,Datatype=1,Units='',UserEditable=False)
        WeekDay.save()
      
def start_DailyTask():
    PublishEvent(Severity=0,Text='Daily task is added to scheduler on the process '+ str(os.getpid()),Persistent=False)
    checkReportAvailability()
    scheduler.add_job(func=checkReportAvailability,trigger='cron',id='checkReportAvailability',hour=0,max_instances=1)
    updateWeekDay()
    scheduler.add_job(func=updateWeekDay,trigger='cron',id='updateWeekDay',hour=0,max_instances=1)
    try:
        scheduler.start()
    except:
        pass

def checkCustomCalculations():
    '''THIS TASK IS RUN EVERY HOUR.
    '''
    from HomeAutomation.models import AdditionalCalculationsModel
    aCALCs=AdditionalCalculationsModel.objects.all()
    #logger.info('The following additional calculations were found: '+ str(aCALCs)) 
    for aCALC in aCALCs:
        #logger.info('The additional calculation '+ str(aCALC) + ' returned ' + str(aCALC.checkTrigger())) 
        if aCALC.checkTrigger():
            aCALC.calculate()
            
def HourlyTask():
    import datetime
    from HomeAutomation.models import MainDeviceVarModel
    PublishEvent(Severity=0,Text='Hourly tasks checked',Persistent=False)
    HomeAutomation.models.checkHourlySchedules(init=True)    
    timestamp=datetime.datetime.now()
    hourDay=timestamp.hour
    try:
        HourDay=MainDeviceVarModel.objects.get(Label='Hour of the day')
        HourDay.update_value(newValue=hourDay,writeDB=True)
        #HourDay.UserEditable=False
    except:
        HourDay=MainDeviceVarModel(Label='Hour of the day',Value=hourDay,Datatype=1,Units='H',UserEditable=False)
        HourDay.save()
    
    checkCustomCalculations()

def start_HourlyTask():
    '''THIS TASK IS RUN EVERY HOUR.
    '''
    HourlyTask()
    HomeAutomation.models.init_Rules()
    PublishEvent(Severity=0,Text='Hourly task is added to scheduler on the process '+ str(os.getpid()),Persistent=False)
    scheduler.add_job(func=HourlyTask,trigger='cron',id='HourlyTask',minute=0,max_instances=1)
    try:
        scheduler.start()
    except:
        pass