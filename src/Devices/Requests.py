import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler

import Devices.GlobalVars
import RemoteDevices.HTTP_client
import RemoteDevices.models
import LocalDevices.models
import LocalDevices.callbacks
import Devices.XML_parser
import Devices.models

import xml.etree.ElementTree as ET

logger = logging.getLogger("project")

scheduler = BackgroundScheduler()

def initialize_polling_remote():
    DVs=RemoteDevices.models.DeviceModel.objects.all()
    if DVs is not None:
        for device in DVs:
            if device.DeviceState=='RUNNING':
                toggle_requests(DeviceName=device.DeviceName,forceDB=True)

def initialize_polling_local():
    DVs=LocalDevices.models.DeviceModel.objects.all()
    if DVs is not None:
        for device in DVs:
            if device.DeviceState=='RUNNING':
                toggle_requests(DeviceName=device.DeviceName,forceDB=True)
                    
def toggle_requests(DeviceName,forceDB=False):
 # creates the jobs to request data from the devices
    #forceDB=True forces the value set in the devicesDB, otherwise toggles it.
    try:
        DV=RemoteDevices.models.DeviceModel.objects.get(DeviceName=DeviceName)
    except RemoteDevices.models.DeviceModel.DoesNotExist: 
        try:
            DV=LocalDevices.models.DeviceModel.objects.get(DeviceName=DeviceName)
        except LocalDevices.models.DeviceModel.DoesNotExist:
            logger.error('TOGGLE-REQUESTS: The device '+DeviceName + ' does not exist in the DB.') 
            return
    deviceName=DV.DeviceName 
    deviceType=DV.Type.Code 
    if DV.Type.Connection=='LOCAL':
        devicePin =DV.IO.pin 
    else:
        deviceIP=DV.DeviceIP 
        deviceCode=DV.DeviceCode 
    sample=DV.Sampletime
    if forceDB==False:
        deviceState=DV.DeviceState #device[4]
    else:
        if DV.DeviceState=='RUNNING':
            deviceState='STOPPED'
        else:
            deviceState='RUNNING'
    xmlroot = ET.parse(Devices.GlobalVars.XML_CONFFILE_PATH).getroot()
    parser=Devices.XML_parser.XMLParser(xmlroot=xmlroot)
    #datagrams=parser.getDatagramsStructureForDeviceType(deviceType=deviceType)
    datagrams=Devices.models.DatagramModel.objects.filter(DeviceType=deviceType)
    
    if deviceState=='STOPPED':
        logger.info('Device '+deviceName+ ' was stopped')    
        for datagram in datagrams:
            datagramID=datagram.Identifier
            if datagram.isSynchronous():#int(datagram['sample'])>0:
                logger.info('Requests '+deviceName+'-'+datagramID+ ' is added to scheduler') 
                if DV.Type.Connection=='LOCAL':
                    callback=getattr(LocalDevices.callbacks, deviceType)(DV).read_sensor # gets the link to the function read_sensor of the appropriate class
                    scheduler.add_job(func=callback,trigger='interval',args=(),
                                      id=deviceName+'-'+datagramID, 
                                      seconds=sample,replace_existing=True)
                else:
                    scheduler.add_job(func=request_to_device,trigger='interval',args=(deviceIP,deviceCode, datagramID),
                                      id=deviceName+'-'+datagramID, 
                                      seconds=sample,replace_existing=True)
        logger.info('Polling for the device '+deviceName+' is started on process ' + str(os.getpid()))  
        try:
            scheduler.start()
        except:
            logger.info('Main thread was already started')
        #updates the state of the device in the DB
        DV.DeviceState='RUNNING'
    else:
        logger.info('Device '+deviceName+ ' was running')   
        logger.info('There are still these polls active '+ str(scheduler.get_jobs()))  
        for datagram in datagrams:
            datagramID=datagram.Identifier
            if datagram.isSynchronous():#int(datagram['sample'])>0:
                id=deviceName+'-'+datagramID
                logger.info('Removing job '+id) 
                try:
                    scheduler.remove_job(id)
                except:
                    logger.error('Job ID '+id+' does not exist. DB mismatch!!') 
        DV.DeviceState='STOPPED'
        logger.info('Polling for the device '+deviceName+' is stopped')  
        logger.info('There are still these polls active '+str(scheduler.get_jobs()))  
    
    DV.save(update_fields=["DeviceState"])

def request_to_device(deviceIP,deviceCode,DatagramId):
    logger.info('Lanzada consulta ' +DatagramId+ ' a ' + deviceIP + ' desde el proceso ' + str(os.getpid()))
    HTTPrequest=RemoteDevices.HTTP_client.HTTP_requests(server='http://'+deviceIP)    
    HTTPrequest.request_datagram(DeviceCode=deviceCode,DatagramId=DatagramId) 
    
# def toggle_HTTP_requests(DeviceName,forceDB=False):
 # # creates the jobs to request data from the devices
    # #forceDB=True forces the value set in the devicesDB, otherwise toggles it.
    # DV=RemoteDevices.models.DeviceModel.objects.get(DeviceName=DeviceName)
    # deviceName=DV.DeviceName #device[0]
    # deviceType=DV.Type.Code #device[1]
    # deviceIP=DV.DeviceIP #device[2]
    # deviceCode=DV.DeviceCode #device[3]
    # sample=DV.Sampletime
    # if forceDB==False:
        # deviceState=DV.DeviceState #device[4]
    # else:
        # if DV.DeviceState=='RUNNING':
            # deviceState='STOPPED'
        # else:
            # deviceState='RUNNING'
    # xmlroot = ET.parse(Devices.GlobalVars.XML_CONFFILE_PATH).getroot()
    # parser=Devices.XML_parser.XMLParser(xmlroot=xmlroot)
    # #datagrams=parser.getDatagramsStructureForDeviceType(deviceType=deviceType)
    # datagrams=Devices.models.DatagramModel.objects.filter(DeviceType=deviceType)
    # logger.info('deviceState= '+deviceState) 
    
    # if deviceState=='STOPPED':
        # logger.info('Device '+deviceName+ ' was stopped')    
        # for datagram in datagrams:
            # #sample=int(datagram['sample'])
            # datagramID=datagram.Identifier
            # if datagram.isSynchronous():#int(datagram['sample'])>0:
                # logger.info('Requests '+deviceName+'-'+datagramID+ ' is added to scheduler') 
                # scheduler.add_job(func=request_to_device,trigger='interval',args=(deviceIP,deviceCode, datagramID),
                                  # id=deviceName+'-'+datagramID, 
                                  # seconds=sample,replace_existing=True)
        # logger.info('Polling for the device '+deviceName+' is started on process ' + str(os.getpid()))  
        # try:
            # scheduler.start()
        # except:
            # logger.info('Main thread was already started')
        # #updates the state of the device in the DB
        # DV.DeviceState='RUNNING'
    # else:
        # logger.info('Device '+deviceName+ ' was running')   
        # logger.info('There are still these polls active '+ str(scheduler.get_jobs()))  
        # for datagram in datagrams:
            # datagramID=datagram.Identifier
            # if datagram.isSynchronous():#int(datagram['sample'])>0:
                # id=deviceName+'-'+datagramID
                # logger.info('Removing job '+id) 
                # try:
                    # scheduler.remove_job(id)
                # except:
                    # logger.error('Job ID '+id+' does not exist. DB mismatch!!') 
        # DV.DeviceState='STOPPED'
        # logger.info('Polling for the device '+deviceName+' is stopped')  
        # logger.info('There are still these polls active '+str(scheduler.get_jobs()))  
    
    # DV.save(update_fields=["DeviceState"])



# def toggle_LOCAL_requests(DeviceName,forceDB=False):
    # DV=LocalDevices.models.DeviceModel.objects.get(DeviceName=DeviceName)
    # deviceName =DV.DeviceName #device[0]
    # deviceType =DV.Type.Code #device[1]
    # devicePin =DV.IO.pin #device[2]
    # sample=DV.Sampletime
    # if forceDB==False:
        # deviceState=DV.DeviceState #device[4]
    # else:
        # if DV.DeviceState=='RUNNING':
            # deviceState='STOPPED'
        # else:
            # deviceState='RUNNING'
    # xmlroot = ET.parse(Devices.GlobalVars.XML_CONFFILE_PATH).getroot()
    # parser=Devices.XML_parser.XMLParser(xmlroot=xmlroot)
    # #datagrams=parser.getDatagramsStructureForDeviceType(deviceType=deviceType)
    # datagrams=Devices.models.DatagramModel.objects.filter(DeviceType=deviceType)
    # logger.info('deviceState= '+deviceState) 
    
    # if deviceState=='STOPPED':
        # logger.info('Device '+deviceName+ ' was stopped')    
        # for datagram in datagrams:
            # datagramID=datagram.Identifier
            # if datagram.isSynchronous():#int(datagram['sample'])>0:
                # logger.info('Requests '+deviceName+'-'+datagramID+ ' is added to scheduler') 
                # callback=getattr(LocalDevices.callbacks, deviceType)(DV).read_sensor # gets the link to the function read_sensor of the appropriate class

                # scheduler.add_job(func=callback,trigger='interval',args=(),
                                  # id=deviceName+'-'+datagramID, 
                                  # seconds=sample,replace_existing=True)
        # logger.info('Polling for the device '+deviceName+' is started on process ' + str(os.getpid()))  
        # try:
            # scheduler.start()
        # except:
            # logger.info('Main thread was already started')
        # #updates the state of the device in the DB
        # DV.DeviceState='RUNNING'
    # else:
        # logger.info('Device '+deviceName+ ' was running')   
        # logger.info('There are still these polls active '+ str(scheduler.get_jobs()))  
        # for datagram in datagrams:
            # datagramID=datagram.Identifier
            # if datagram.isSynchronous():#int(datagram['sample'])>0:
                # id=deviceName+'-'+datagramID
                # logger.info('Removing job '+id) 
                # try:
                    # scheduler.remove_job(id)
                # except:
                    # logger.error('Job ID '+id+' does not exist. DB mismatch!!') 
        # DV.DeviceState='STOPPED'
        # logger.info('Polling for the device '+deviceName+' is stopped')  
        # logger.info('There are still these polls active '+str(scheduler.get_jobs()))  
    
    # DV.save(update_fields=["DeviceState"])
        
        