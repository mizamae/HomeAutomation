import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler
import apscheduler.events as events
import HomeAutomation.models
import Devices.GlobalVars
import Devices.BBDD

from Events.consumers import PublishEvent

logger = logging.getLogger("project")

scheduler = BackgroundScheduler()   
url = 'sqlite:///TasksScheduler.sqlite'
scheduler.add_jobstore('sqlalchemy', url=url)
                
def my_listener(event):
    pass
    if event.exception:
        try:
            text='The scheduled task '+event.job_id+' reported an error: ' + str(event.traceback) 
        except:
            text='Error on scheduler: ' + str(event.exception)
        PublishEvent(Severity=4,Text=text,Persistent=True)
    else:
        pass

scheduler.add_listener(callback=my_listener, mask=events.EVENT_JOB_EXECUTED | events.EVENT_JOB_ERROR)

try:
    scheduler.start()
except BaseException as e:
    logger.info('Exception Tasks APS: ' + str(e))

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
    id='registerDBcompact'
    scheduler.add_job(func=compactRegistersDB,trigger='cron',id=id,day='last',hour=0,minute=0,max_instances=1,coalesce=True,misfire_grace_time=600,replace_existing=True)
    JOB=scheduler.get_job(job_id=id)
    PublishEvent(Severity=0,Text='Task '+id+ ' is added to scheduler: ' + str(JOB),Persistent=False)


def checkReportAvailability():
    '''THIS TASK IS RUN EVERY DAY AT HOUR 0 AND CHECKS IF ANY REPORT TRIGGERING CONDITION IS MET.
    IN CASE SO, IT GENERATES THE REPORT.
    '''
    from Devices.models import ReportModel,ReportItems
    import json
    reports=ReportModel.objects.all()
    for report in reports:
        if report.checkTrigger():
            report.generate()

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
    #checkReportAvailability()
    id='checkReportAvailability'
    scheduler.add_job(func=checkReportAvailability,trigger='cron',id=id,hour=0,max_instances=1,coalesce=True,misfire_grace_time=30,replace_existing=True)
    JOB=scheduler.get_job(job_id=id)
    PublishEvent(Severity=0,Text='Task '+id+ ' is added to scheduler: ' + str(JOB),Persistent=False)
    #updateWeekDay()
    id='updateWeekDay'
    scheduler.add_job(func=updateWeekDay,trigger='cron',id=id,hour=0,max_instances=1,coalesce=True,misfire_grace_time=30,replace_existing=True)
    JOB=scheduler.get_job(job_id=id)
    PublishEvent(Severity=0,Text='Task '+id+ ' is added to scheduler: ' + str(JOB),Persistent=False)


def checkCustomCalculations():
    '''THIS TASK IS RUN EVERY HOUR.
    '''
    from HomeAutomation.models import AdditionalCalculationsModel
    aCALCs=AdditionalCalculationsModel.objects.all()
    for aCALC in aCALCs:
        if aCALC.checkTrigger():
            #PublishEvent(Severity=0,Text=str(aCALC)+' evaluated to True',Persistent=True)
            aCALC.calculate()
            
def HourlyTask():
    import datetime
    from HomeAutomation.models import MainDeviceVarModel
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
    #updateWeekDay()
    checkCustomCalculations()

def start_HourlyTask():
    '''THIS TASK IS RUN EVERY HOUR.
    '''
    #HourlyTask()
    #HomeAutomation.models.init_Rules()
    id='HourlyTask'
    scheduler.add_job(func=HourlyTask,trigger='cron',id=id,minute=0,max_instances=1,coalesce=True,misfire_grace_time=30,replace_existing=True)
    JOB=scheduler.get_job(job_id=id)
    PublishEvent(Severity=0,Text='Task '+id+ ' is added to scheduler: ' + str(JOB),Persistent=False)
    id='afterBoot'
    scheduler.add_job(func=run_afterBoot,trigger='interval',id=id,seconds=10,max_instances=1,coalesce=True,misfire_grace_time=30,replace_existing=True)

def run_afterBoot():
    id='afterBoot'
    scheduler.remove_job(id)
    HomeAutomation.models.init_Rules()
    HourlyTask()
    updateWeekDay()
    from Devices.Requests import initialize_polling_devices
    initialize_polling_devices()