
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
def renewSSLCertificate():  
    try:
        # Switch to Python2
        os.system("sudo ln -sf /usr/bin/python2 /usr/bin/python")
        os.system("sudo /home/pi/HomeAutomation/src/utils/certbot-auto renew")
        message="SSL certificates renewed OK"
        s=0
    except Exception as e:
        logger.error('Exception Tasks RenewSSL: ' + str(e))
        message="Error renewing SSL certificates: " + str(e)
        s=10
    # Switch to Python3
    os.system("sudo ln -sf /usr/bin/python3 /usr/bin/python")
    PublishEvent(Severity=s,Text=message,
                 Code='Tasks-SSL',Persistent=True)
    
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
    
    renewSSLCertificate()
            
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
    except:
        WeekDay=MainDeviceVars(Label='Day of the week',Value=weekDay,DataType=DTYPE_INTEGER,Units='',UserEditable=False)
        WeekDay.store2DB()
    WeekDay.updateValue(newValue=weekDay,writeDB=True)

def DailyTask():
    from MainAPP.models import SiteSettings
    from MainAPP.constants import GIT_PATH
    updateWeekDay()
    checkReportAvailability()
    SETTINGS=SiteSettings.load()
    SETTINGS.dailyTasks()
        
def start_DailyTask():
    id='DailyTask'
    scheduler.add_job(func=DailyTask,trigger='cron',id=id,hour=0,max_instances=1,coalesce=True,misfire_grace_time=60*60*6,replace_existing=True)
    JOB=scheduler.get_job(job_id=id)
    PublishEvent(Severity=0,Text='Task '+id+ ' is added to scheduler: ' + str(JOB),Persistent=False,Code='Tasks-D')

### HOURLY FUNCTIONS
def updateDNS():
    try:
        # Switch to Python2
        #os.system("sudo ln -sf /usr/bin/python2 /usr/bin/python")
        os.system("sudo /usr/local/bin/noip2")
    except Exception as e:
        logger.error('Exception Tasks updateDNS: ' + str(e))
    # Switch to Python3
    #os.system("sudo ln -sf /usr/bin/python3 /usr/bin/python")
    
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
    except:
        HourDay=MainDeviceVars(Label='Hour of the day',Value=hourDay,DataType=DTYPE_INTEGER,Units='H',UserEditable=False)
        HourDay.store2DB()
    HourDay.updateValue(newValue=hourDay,writeDB=True)
    AutomationVarWeeklySchedules.checkAll(init=True)
    checkCustomCalculations()
    updateDNS()

def start_HourlyTask():
    id='HourlyTask'
    scheduler.add_job(func=HourlyTask,trigger='cron',id=id,minute=0,max_instances=1,coalesce=True,misfire_grace_time=40*60,replace_existing=True)
    JOB=scheduler.get_job(job_id=id)
    PublishEvent(Severity=0,Text='Task '+id+ ' is added to scheduler: ' + str(JOB),Persistent=False,Code='Tasks-H')
    id='afterBoot'
    scheduler.add_job(func=run_afterBoot,trigger='interval',id=id,seconds=10,max_instances=1,coalesce=True,misfire_grace_time=10,replace_existing=True)


def run_afterBoot():
    id='afterBoot'
    scheduler.remove_job(id)
    from MainAPP.models import AutomationRules,AutomationVarWeeklySchedules
    AutomationRules.initAll()
    AutomationVarWeeklySchedules.initialize()
    from DevicesAPP.models import initialize_polling_devices,MasterGPIOs
    initialize_polling_devices()
    MasterGPIOs.initializeIOs(declareInputEvent=True)
    HourlyTask()
    updateWeekDay()
    from utils.asynchronous_tasks import BackgroundTimer
    from DevicesAPP.constants import POLLING_WATCHDOG_TIMER,POLLING_WATCHDOG_VAR
    #process=BackgroundTimer(callable=WatchDog,threadName='WatchDog',interval=POLLING_WATCHDOG_TIMER,repeat=True)
    from utils.Watchdogs import WATCHDOG
    process=WATCHDOG(name='PollingWatchdog',interval=POLLING_WATCHDOG_TIMER,cachevar=POLLING_WATCHDOG_VAR)

#     SCRIPT TO INITIALIZE THE DB WITH DATA FROM BEGINING OF THE YEAR
#     from DevicesAPP.callbacks import ESIOS
#     from DevicesAPP.models import Devices
#     DV=Devices.objects.filter(DVT__Code='ESIOS')
#     instance=ESIOS(DV[0])
#     import datetime
#     instance(datagramId = 'energy_cost',date=datetime.datetime(year=2018,month=10,day=8))
#     instance.initializeDB(fromdate=datetime.datetime(year=2017,month=12,day=31),datagramId = 'energy_cost')
#      

#     SCRIPT TO INITIALIZE THE DB WITH DATA FROM BEGINING OF THE YEAR
    import DevicesAPP.callbacks
    DevicesAPP.callbacks.PENDING_DB.runOnInit()
    from DevicesAPP.models import DeviceTypes,Devices
    from DevicesAPP.constants import RUNNING_STATE
    # EXECUTES THE METHOD ON INIT ON EVERY CLASS THAT PROVIDES IT ON DEVICES.CALLBACKS
    import inspect
    classes=[m[0] for m in inspect.getmembers(DevicesAPP.callbacks, inspect.isclass) if m[1].__module__ == 'DevicesAPP.callbacks']
    for object in classes:
        class_=getattr(DevicesAPP.callbacks,object)
        if callable(getattr(class_, "runOnInit", None)):
            try:
                DVT=DeviceTypes.objects.get(Code=class_.__name__)
            except DeviceTypes.DoesNotExist:
                DVT = None
            
            if DVT!=None:
                DVs=Devices.objects.filter(DVT=DVT,State=RUNNING_STATE)
                for DV in DVs:
                    class_.runOnInit(DV=DV)
    
    #import datetime
    #from DevicesAPP.models import Devices
    #DV=Devices.objects.filter(DVT__Code='IBERDROLA')
    #instance=DevicesAPP.callbacks.IBERDROLA(DV[0])
    #instance(date=datetime.datetime(year=2018,month=10,day=7),datagramId = 'dailyconsumption')
    #instance.getSingleDay(date=datetime.datetime(year=2018,month=11,day=5),datagramId = 'dailyconsumption')
    #instance.initializeDB(fromdate=datetime.datetime(year=2018,month=11,day=2),datagramId = 'dailyconsumption')
    