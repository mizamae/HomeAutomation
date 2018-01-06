import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler
import apscheduler.events as events
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
import datetime
from tzlocal import get_localzone

import Devices.GlobalVars
import Devices.callbacks
from Devices.callbacks import callback_handler
import Devices.XML_parser
import Devices.models
import Devices.HTTP_client
import Devices.BBDD
from Events.consumers import PublishEvent

import xml.etree.ElementTree as ET

logger = logging.getLogger("project")

scheduler = BackgroundScheduler()
url = 'sqlite:///scheduler.sqlite'
scheduler.add_jobstore('sqlalchemy', url=url)

try:
    scheduler.start()
except BaseException as e:
    logger.info('Exception APS: ' + str(e))
                
def my_listener(event):
    pass
    # logger.debug("APS: " + str(event.traceback))
    # logger.debug("APS: " + str(event.exception))
    if event.exception:
        try:
            text='The scheduled task '+event.job_id+' reported an error: ' + str(event.traceback) 
        except:
            text='Error on scheduler: ' + str(event.exception)
        PublishEvent(Severity=4,Text=text,Persistent=True)
    else:
        pass

scheduler.add_listener(callback=my_listener, mask=events.EVENT_JOB_EXECUTED | events.EVENT_JOB_ERROR)

def initialize_polling_devices():
    DVs=Devices.models.DeviceModel.objects.all()
    if DVs is not None:
        for DV in DVs:
            if DV.DeviceState==1:
                update_requests(DV=DV)

                    
def update_requests(DV):
 # creates the jobs to request data from the devices
    #datagrams=parser.getDatagramsStructureForDeviceType(deviceType=deviceType)
    DGs=Devices.models.DatagramModel.objects.filter(DeviceType=DV.Type)
    AppDB=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                           configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH,year='')
    now=timezone.now()
    next_run_time = now + datetime.timedelta(seconds=10)
    tables=DV.getRegistersTables()
    local_tz=get_localzone()
    #executeNow=False
    if len(tables)>0:
        for table in tables:                                       
            sql='SELECT timestamp FROM "'+ table +'" ORDER BY timestamp DESC LIMIT 1'
            row=AppDB.registersDB.retrieve_from_table(sql=sql,single=True,values=(None,))
            if row!=None:
                localdate = local_tz.localize(row[0])
                if now-localdate > datetime.timedelta(seconds=DV.Sampletime):
                    executeNow=True
                    break
                else:
                    executeNow=False
            else:
                executeNow=True
                break
    else:
        executeNow=False
        
    if DV.DeviceState==1:
        for DG in DGs:
            datagramID=DG.Identifier
            if DG.isSynchronous():#int(datagram['sample'])>0:
                id=DV.DeviceName+'-'+DG.Identifier
                SCHD=scheduler.get_job(job_id=id,jobstore='DevicesPolling')                   
                
                if DV.Type.Connection=='LOCAL':
                    callback=callback_handler
                    if executeNow:
                        scheduler.add_job(func=callback,trigger='interval',
                                      id=id, next_run_time=next_run_time,args=[getattr(Devices.callbacks, DV.Type.Code)(DV),],
                                      seconds=DV.Sampletime,replace_existing=True,max_instances=1,coalesce=True)
                    else:  
                        scheduler.add_job(func=callback,trigger='interval',
                                      id=id,args=[getattr(Devices.callbacks, DV.Type.Code)(DV),], 
                                      seconds=DV.Sampletime,replace_existing=True,max_instances=1,coalesce=True)
                        
                elif DV.Type.Connection=='REMOTE':
                    if executeNow:
                        scheduler.add_job(func=request_to_device,trigger='interval',args=(DV.DeviceIP,DV.DeviceCode, DG.Identifier),
                                      id=id, next_run_time=next_run_time, 
                                      seconds=DV.Sampletime,replace_existing=True,max_instances=1,coalesce=True)
                    else:
                        scheduler.add_job(func=request_to_device,trigger='interval',args=(DV.DeviceIP,DV.DeviceCode, DG.Identifier),
                                      id=id,
                                      seconds=DV.Sampletime,replace_existing=True,max_instances=1,coalesce=True)
                                      
                elif DV.Type.Connection=='MEMORY':
                    callback=callback_handler
                    arguments={'datagram':DG.Identifier}
                    if executeNow:
                        scheduler.add_job(func=callback,trigger='interval',kwargs=arguments,
                                      id=id, next_run_time=next_run_time, args=[getattr(Devices.callbacks, DV.Type.Code)(DV),], 
                                      seconds=DV.Sampletime,replace_existing=True,max_instances=1,coalesce=True)
                    else:
                        scheduler.add_job(func=callback,trigger='interval',kwargs=arguments,
                                      id=id, args=[getattr(Devices.callbacks, DV.Type.Code)(DV),], 
                                      seconds=DV.Sampletime,replace_existing=True,max_instances=1,coalesce=True)
                
                JOBs=scheduler.get_jobs()
                for JOB in JOBs:
                    if JOB.id==id: 
                        PublishEvent(Severity=0,Text='Requests '+id+ ' is added to scheduler: ' + str(JOB),Persistent=False)
                        break
            
        if len(DGs)>0:
            text=str(_('Polling for the device '))+DV.DeviceName+str(_(' is started with sampletime= ')) + str(DV.Sampletime)  
            PublishEvent(Severity=0,Text=text,Persistent=False)
        else:
            logger.warning('The device types ' +str(DV.Type) + ' have no datagrams defined')
        #updates the state of the device in the DB
        
    else:
        logger.info('There are still these polls active '+ str(scheduler.get_jobs()))  
        for DG in DGs:
            if DG.isSynchronous():#int(datagram['sample'])>0:
                id=DV.DeviceName+'-'+DG.Identifier
                logger.info('Removing job '+id)
                try:
                    scheduler.remove_job(id)
                except:
                    logger.error('Job ID '+id+' does not exist!!')   
        text=str(_('Polling for the device '))+DV.DeviceName+str(_(' is stopped ')) 
        PublishEvent(Severity=0,Text=text,Persistent=True)
        
    

def request_to_device(deviceIP,deviceCode,DatagramId):
    #text=str(_('Sent request ')) +DatagramId+ str(_(' to ')) + deviceIP
    #PublishEvent(Severity=0,Text=text,Persistent=False)
    HTTPrequest=Devices.HTTP_client.HTTP_requests(server='http://'+deviceIP)    
    HTTPrequest.request_datagram(DeviceCode=deviceCode,DatagramId=DatagramId) 
  