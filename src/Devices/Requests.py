import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
import datetime
from tzlocal import get_localzone

import Devices.GlobalVars
import Devices.callbacks
import Devices.XML_parser
import Devices.models
import Devices.HTTP_client
import Devices.BBDD
from Events.consumers import PublishEvent

import xml.etree.ElementTree as ET

logger = logging.getLogger("project")

scheduler = BackgroundScheduler()

   
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
    tables=DV.getRegistersTables()
    local_tz=get_localzone()
    
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
    executeNow=False
    if DV.DeviceState==1:
        for DG in DGs:
            datagramID=DG.Identifier
            if DG.isSynchronous():#int(datagram['sample'])>0:
                id=DV.DeviceName+'-'+DG.Identifier
                try:
                    scheduler.remove_job(id)
                    logger.info('Killed previous job ID '+id)
                except:
                    pass 
                    
                
                if DV.Type.Connection=='LOCAL':
                    callback=getattr(Devices.callbacks, DV.Type.Code)(DV).read_sensor # gets the link to the function read_sensor of the appropriate class
                    scheduler.add_job(func=callback,trigger='interval',args=(),
                                      id=id, 
                                      seconds=DV.Sampletime,replace_existing=True,max_instances=1)
                    if executeNow:
                        arguments={}
                        #callback(**arguments)
                        
                elif DV.Type.Connection=='REMOTE':
                    scheduler.add_job(func=request_to_device,trigger='interval',args=(DV.DeviceIP,DV.DeviceCode, DG.Identifier),
                                      id=id, 
                                      seconds=DV.Sampletime,replace_existing=True,max_instances=1)
                    if executeNow:
                        request_to_device(DV.DeviceIP,DV.DeviceCode, DG.Identifier)
                elif DV.Type.Connection=='MEMORY':
                    callback=getattr(Devices.callbacks, DV.Type.Code)(DV).read_sensor # gets the link to the function read_sensor of the appropriate class
                    arguments={'datagram':DG.Identifier}
                    scheduler.add_job(func=callback,trigger='interval',kwargs=arguments,
                                      id=id, 
                                      seconds=DV.Sampletime,replace_existing=True,max_instances=1)
                    if executeNow:
                        callback(**arguments)
                logger.info('Requests '+id+ ' is added to scheduler') 
        if len(DGs)>0:
            text=str(_('Polling for the device '))+DV.DeviceName+str(_(' is started with sampletime= ')) + str(DV.Sampletime)  
            PublishEvent(Severity=0,Text=text,Persistent=True)
            try:
                scheduler.start()
            except:
                logger.info('Main thread was already started')
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
    text=str(_('Sent request ')) +DatagramId+ str(_(' to ')) + deviceIP
    PublishEvent(Severity=0,Text=text,Persistent=False)
    HTTPrequest=Devices.HTTP_client.HTTP_requests(server='http://'+deviceIP)    
    HTTPrequest.request_datagram(DeviceCode=deviceCode,DatagramId=DatagramId) 
  