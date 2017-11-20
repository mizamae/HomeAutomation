import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler

import Devices.GlobalVars
import Devices.callbacks
import Devices.XML_parser
import Devices.models

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
                    
                logger.info('Requests '+id+ ' is added to scheduler') 
                if DV.Type.Connection=='LOCAL':
                    callback=getattr(Devices.callbacks, DV.Type.Code)(DV).read_sensor # gets the link to the function read_sensor of the appropriate class
                    scheduler.add_job(func=callback,trigger='interval',args=(),
                                      id=id, 
                                      seconds=DV.Sampletime,replace_existing=True)
                elif DV.Type.Connection=='REMOTE':
                    scheduler.add_job(func=request_to_device,trigger='interval',args=(DV.DeviceIP,DV.DeviceCode, DG.Identifier),
                                      id=id, 
                                      seconds=DV.Sampletime,replace_existing=True)
                elif DV.Type.Connection=='MEMORY':
                    callback=getattr(Devices.callbacks, DV.Type.Code)(DV).read_sensor # gets the link to the function read_sensor of the appropriate class
                    arguments={'datagram':'observation'}
                    scheduler.add_job(func=callback,trigger='interval',kwargs=arguments,
                                      id=id, 
                                      seconds=DV.Sampletime,replace_existing=True)
        if len(DGs)>0:
            logger.info('Polling for the device '+DV.DeviceName+' is started on process ' + str(os.getpid()) + ' with sampletime= ' + str(DV.Sampletime))  
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
                    logger.error('Job ID '+id+' does not exist. DB mismatch!!') 
        logger.info('Polling for the device '+DV.DeviceName+' is stopped')  
        logger.info('There are still these polls active '+str(scheduler.get_jobs()))  

def request_to_device(deviceIP,deviceCode,DatagramId):
    logger.info('Lanzada consulta ' +DatagramId+ ' a ' + deviceIP + ' desde el proceso ' + str(os.getpid()))
    HTTPrequest=Devices.HTTP_client.HTTP_requests(server='http://'+deviceIP)    
    HTTPrequest.request_datagram(DeviceCode=deviceCode,DatagramId=DatagramId) 
  