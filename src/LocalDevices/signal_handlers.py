from LocalDevices.models import DeviceModel
import Devices.BBDD
import Devices.GlobalVars
import Devices.Requests


import logging
logger = logging.getLogger("project")

def datagram_reception_handler(sender, **kwargs):
    deviceName=kwargs['DeviceName']
    values=kwargs['values']
    sensor=DeviceModel.objects.get(DeviceName=deviceName)
    sensor.Connected=True
    sensor.LastUpdated=values['timestamp']
    sensor.save(update_fields=["Connected","LastUpdated"])
    #logger.info("SIGNALS: The device "+ deviceName+" responded with values= "+str(values))
    
def datagram_exception_handler(sender, **kwargs):
    deviceName=kwargs['DeviceName']
    Error=kwargs['Error']
    logger.error("SIGNALS: The device "+ deviceName+" raised an error: "+str(Error))

def Toggle_DeviceStatus_handler(sender,**kwargs):
    devicename=kwargs['DeviceName']
    Devices.Requests.toggle_requests(DeviceName=devicename)
    sensor=DeviceModel.objects.get(DeviceName=devicename)
    logger.info('SIGNALS: The status of ' +devicename+' has changed to '+sensor.DeviceState + '.')

def DeviceName_changed_handler(sender,**kwargs):
    OLDdeviceName=kwargs['OldDeviceName']
    NEWdeviceName=kwargs['NewDeviceName']
    logger.info("SIGNALS: Ha cambiado el nombre del dispositivo " +OLDdeviceName+". Ahora se llama " + NEWdeviceName)
    applicationDBs=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                      configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH)   
    applicationDBs.rename_DeviceRegister_tables(OldDeviceName=OLDdeviceName,NewDeviceName=NEWdeviceName)