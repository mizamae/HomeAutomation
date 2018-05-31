
import os
from django.utils.translation import ugettext_lazy as _
from apscheduler.schedulers.background import BackgroundScheduler
import apscheduler.events as events

from MainAPP.constants import REGISTERS_DB_PATH,MANAGEMENT_TASKS_SCHEDULER_URL

from EventsAPP.consumers import PublishEvent

import logging
logger = logging.getLogger("project")

scheduler = BackgroundScheduler()   
url = MANAGEMENT_TASKS_SCHEDULER_URL
scheduler.add_jobstore('sqlalchemy', url=url)
                
def my_listener(event):
    pass
    if event.exception:
        try:
            text='The scheduled task '+event.job_id+' reported an error: ' + str(event.traceback) 
        except:
            text='Error on scheduler: ' + str(event.exception)
        PublishEvent(Severity=4,Text=text,Persistent=False,Code='TaskAPS-100')
    else:
        pass

scheduler.add_listener(callback=my_listener, mask=events.EVENT_JOB_EXECUTED | events.EVENT_JOB_ERROR)

try:
    scheduler.start()
except BaseException as e:
    logger.info('Exception Tasks APS: ' + str(e))


### MONTHLY FUNCTIONS
def compactRegistersDB():
    import datetime
    now=datetime.datetime.now()-datetime.timedelta(hours=1)
    from utils.BBDD import compactRegistersDB
    result=compactRegistersDB(year=now.year)
    sizep=result['initial_size']
    size=result['final_size']
    PublishEvent(Severity=0,Text='The DB size is reduced from ' +str(sizep/1000) + ' to ' + str(size/1000) + ' kB after compactation',
                 Code='Tasks-M_0',Persistent=True)

def MonthlyTask():
    compactRegistersDB()
    from utils.GoogleDrive import GoogleDriveWrapper
    instance=GoogleDriveWrapper()
    autenticated=instance.checkCredentials()
    if autenticated:
        instance.uploadDBs()
        PublishEvent(Severity=0,Text=_("DBs uploaded to GDrive"),Persistent=True,Code='Tasks-1_1')
    else:
        PublishEvent(Severity=0,Text=_("Unable to autenticate to GDrive"),Persistent=True,Code='Tasks-M_1')
            
def start_MonthlyTask(): 
    '''COMPACTS THE REGISTER'S TABLE MONTHLY ON THE LAST DAY OF THE MONTH AT 00:00:00
    '''  
    id='MonthlyTask'
    scheduler.add_job(func=MonthlyTask,trigger='cron',id=id,day='last',hour=0,minute=0,max_instances=1,coalesce=True,misfire_grace_time=600,replace_existing=True)
    JOB=scheduler.get_job(job_id=id)
    PublishEvent(Severity=0,Text='Task '+id+ ' is added to scheduler: ' + str(JOB),Persistent=False,Code='Tasks-M')


### DAILY FUNCTIONS
def checkReportAvailability():
    '''THIS TASK IS RUN EVERY DAY AT HOUR 0 AND CHECKS IF ANY REPORT TRIGGERING CONDITION IS MET.
    IN CASE SO, IT GENERATES THE REPORT.
    '''
    from ReportingAPP.models import Reports,ReportItems
    import json
    reports=Reports.objects.all()
    for report in reports:
        if report.checkTrigger():
            report.generate()

def updateWeekDay():
    import datetime
    from DevicesAPP.models import MainDeviceVars
    from DevicesAPP.constants import DTYPE_INTEGER
    timestamp=datetime.datetime.now()
    weekDay=timestamp.weekday()
    try:
        WeekDay=MainDeviceVars.objects.get(Label='Day of the week')
        WeekDay.updateValue(newValue=weekDay,writeDB=True)
    except:
        WeekDay=MainDeviceVars(Label='Day of the week',Value=weekDay,DataType=DTYPE_INTEGER,Units='',UserEditable=False)
        WeekDay.store2DB()

def DailyTask():
    from MainAPP.models import SiteSettings
    updateWeekDay()
    checkReportAvailability()
    SETTINGS=SiteSettings.load()
    SETTINGS.dailyTasks()
        
def start_DailyTask():
    id='DailyTask'
    scheduler.add_job(func=DailyTask,trigger='cron',id=id,hour=0,max_instances=1,coalesce=True,misfire_grace_time=30,replace_existing=True)
    JOB=scheduler.get_job(job_id=id)
    PublishEvent(Severity=0,Text='Task '+id+ ' is added to scheduler: ' + str(JOB),Persistent=False,Code='Tasks-D')

### HOURLY FUNCTIONS
def checkCustomCalculations():
    '''THIS TASK IS RUN EVERY HOUR.
    '''
    from MainAPP.models import AdditionalCalculations
    aCALCs=AdditionalCalculations.objects.all()
    for aCALC in aCALCs:
        if aCALC.checkTrigger():
            aCALC.calculate()
            
def HourlyTask():
    '''THIS TASK IS RUN EVERY HOUR.
    '''
    import datetime
    from DevicesAPP.models import MainDeviceVars
    from MainAPP.models import AutomationVarWeeklySchedules
    from DevicesAPP.constants import DTYPE_INTEGER
    timestamp=datetime.datetime.now()
    hourDay=timestamp.hour
    try:
        HourDay=MainDeviceVars.objects.get(Label='Hour of the day')
        HourDay.updateValue(newValue=hourDay,writeDB=True)
    except:
        HourDay=MainDeviceVars(Label='Hour of the day',Value=hourDay,DataType=DTYPE_INTEGER,Units='H',UserEditable=False)
        HourDay.store2DB()
    AutomationVarWeeklySchedules.checkAll(init=True)
    checkCustomCalculations()

def start_HourlyTask():
    id='HourlyTask'
    scheduler.add_job(func=HourlyTask,trigger='cron',id=id,minute=0,max_instances=1,coalesce=True,misfire_grace_time=30,replace_existing=True)
    JOB=scheduler.get_job(job_id=id)
    PublishEvent(Severity=0,Text='Task '+id+ ' is added to scheduler: ' + str(JOB),Persistent=False,Code='Tasks-H')
    id='afterBoot'
    scheduler.add_job(func=run_afterBoot,trigger='interval',id=id,seconds=10,max_instances=1,coalesce=True,misfire_grace_time=5,replace_existing=True)

def run_afterBoot():
    id='afterBoot'
    scheduler.remove_job(id)
    HourlyTask()
    updateWeekDay()
    from MainAPP.models import AutomationRules,AutomationVarWeeklySchedules
    AutomationRules.initAll()
    AutomationVarWeeklySchedules.initialize()
    from DevicesAPP.models import initialize_polling_devices,MasterGPIOs
    initialize_polling_devices()
    MasterGPIOs.initializeIOs(declareInputEvent=True)
    