import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler
import apscheduler.events as events
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
import datetime
from tzlocal import get_localzone

import Devices.GlobalVars
import Devices.XML_parser
import Devices.models

import Devices.BBDD
from Events.consumers import PublishEvent

import xml.etree.ElementTree as ET

logger = logging.getLogger("project")

scheduler = BackgroundScheduler()
url = 'sqlite:///scheduler.sqlite'
scheduler.add_jobstore('sqlalchemy', url=url)
# logging.basicConfig()
# logging.getLogger('apscheduler.scheduler').setLevel(logging.DEBUG)
                
def my_listener(event):
    if event.exception:
        try:
            text='The scheduled task '+event.job_id+' reported an error: ' + str(event.traceback) 
            logger.info("APS: " + str(event.traceback))
        except:
            text='Error on scheduler: ' + str(event.exception)
            logger.info("APS: " + str(event.exception))
        PublishEvent(Severity=4,Text=text,Persistent=True)
        initialize_polling_devices()
    else:
        pass

scheduler.add_listener(callback=my_listener, mask=events.EVENT_JOB_EXECUTED | events.EVENT_JOB_ERROR)

try:
    scheduler.start()
except BaseException as e:
    logger.info('Exception APS: ' + str(e))
    
def initialize_polling_devices():
    JOBs=scheduler.get_jobs()
    
    DVs=Devices.models.DeviceModel.objects.all()
    if DVs is not None:
        for DV in DVs:
            if DV.DeviceState==1:
                DV.startPolling()
            else:
                DV.stopPolling()

                    
def update_requests(DV):
 # creates the jobs to request data from the devices
    #datagrams=parser.getDatagramsStructureForDeviceType(deviceType=deviceType)
    #DGs=Devices.models.DatagramModel.objects.filter(DeviceType=DV.Type)
    AppDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                           configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')
    now=timezone.now()
    import random
    next_run_time = now + datetime.timedelta(seconds=random.uniform(10,60))
    tables=DV.getRegistersTables()
    local_tz=get_localzone()
    #executeNow=False
    # if len(tables)>0:
        # for table in tables:                                       
            # sql='SELECT timestamp FROM "'+ table +'" ORDER BY timestamp DESC LIMIT 1'
            # row=AppDB.registersDB.retrieve_from_table(sql=sql,single=True,values=(None,))
            # if row!=None:
                # localdate = local_tz.localize(row[0])
                # localdate=localdate+localdate.utcoffset()
                # if now-localdate > datetime.timedelta(seconds=DV.Sampletime):
                    # executeNow=True
                    # break
                # else:
                    # executeNow=False
            # else:
                # executeNow=True
                # break
    # else:
        # executeNow=False
    executeNow=False
    
    jobIDs=DV.getPollingJobIDs()
    
    if DV.DeviceState==1:
        if jobIDs != []:
            for job in jobIDs:      
                id=job['id']
                DG=job['DG']
                JOB=scheduler.get_job(job_id=id)
                if JOB==None:                     
                    if DV.Type.Connection=='LOCAL': 
                        scheduler.add_job(func=request_to_device,trigger='interval',
                                      id=id,args=(DV,DG,id), 
                                      seconds=DV.Sampletime,replace_existing=True,max_instances=1,coalesce=True,misfire_grace_time=30)
                    elif DV.Type.Connection=='REMOTE':   
                        scheduler.add_job(func=request_to_device,trigger='interval',
                                      id=id,args=(DV, DG, id),
                                      seconds=DV.Sampletime,replace_existing=True,max_instances=1,coalesce=True,misfire_grace_time=30)
                    elif DV.Type.Connection=='MEMORY':
                        kwargs={'datagram':DG.Identifier}
                        scheduler.add_job(func=request_to_device,trigger='interval',
                                      id=id,args=(DV,DG,id), kwargs=kwargs,
                                      seconds=DV.Sampletime,replace_existing=True,max_instances=1,coalesce=True,misfire_grace_time=30)
                    JOB=scheduler.get_job(job_id=id)
                    if JOB!=None: 
                        text=str(_('Polling for the device '))+DV.DeviceName+str(_(' is started with sampletime= ')) + str(DV.Sampletime) + str(_('[s]. Next request at ') + str(JOB.next_run_time))
                        PublishEvent(Severity=0,Text=text,Persistent=True)
                    else:
                        PublishEvent(Severity=4,Text='Error adding job '+id+ ' to scheduler. Polling for device ' +DV.DeviceName+' could not be started' ,Persistent=True)
                        DV.DeviceState=0
                        DV.save()
                else:
                    PublishEvent(Severity=0,Text='Requests '+id+ ' already was in the scheduler. ' + str(_('Next request at ') + str(JOB.next_run_time)),Persistent=True)
        else:        
            DV.DeviceState=0
            DV.save()
            text=str(_('Polling for device '))+DV.DeviceName+str(_(' could not be started. It has no Datagrams defined '))
            PublishEvent(Severity=3,Text=text,Persistent=True)
        #updates the state of the device in the DB
        
    else:
        for job in jobIDs:
            id=job['id']
            JOB=scheduler.get_job(job_id=id)
            if JOB!=None: 
                scheduler.remove_job(id)
                JOBs=scheduler.get_jobs()
                if JOB in JOBs:
                    DV.DeviceState=1
                    DV.save()
                    text='Polling for the device '+DV.DeviceName+' could not be stopped '
                    severity=5
                else:
                    text='Polling for the device '+DV.DeviceName+' is stopped ' 
                    severity=0
                
            else:
                text=str(_('Requests DB mismatch. Job ')) + id + str(_(' did not exist.')) 
                severity=5  
            
            PublishEvent(Severity=severity,Text=text,Persistent=True)
       

    
def request_to_device(DV,DG,jobID,**kwargs):        
    if (DV.Type.Connection=='LOCAL' or DV.Type.Connection=='MEMORY'):
        import Devices.callbacks
        class_=getattr(Devices.callbacks, DV.Type.Code)
        instance=class_(DV)
        instance(**kwargs)
    elif DV.Type.Connection=='REMOTE':
        import Devices.HTTP_client
        HTTPrequest=Devices.HTTP_client.HTTP_requests(server='http://'+DV.DeviceIP)    
        HTTPrequest.request_datagram(DeviceCode=DV.DeviceCode,DatagramId=DG.Identifier) 
    DV.setNextUpdate(jobID=jobID)
    