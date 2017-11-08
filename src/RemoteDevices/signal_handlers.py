from django.db.models import Q

import logging
import Devices.BBDD
import Devices.GlobalVars
import Devices.Requests
import Devices.models
import HomeAutomation.models

logger = logging.getLogger("project")

def Device_datagram_reception_handler(sender, **kwargs):
    timestamp=kwargs['timestamp']
    DV=kwargs['Device']
    datagramID=kwargs['DatagramId']
    datagramInfo=Devices.models.getDatagramStructure(devicetype=DV.Type,ID=datagramID)
    #{'ID':datagramID,'names':names,'types':types,'datatypes':datatypes,'sample':sample}
    for var in datagramInfo['names']:
        rules=HomeAutomation.models.AutomationRuleModel.objects.filter((Q(Var1__Tag=var) & Q(Var1__Device=DV.DeviceName)) | (Q(Var2__Tag=var) & Q(Var2__Device=DV.DeviceName)))
        if len(rules)>0:
            for rule in rules:
                rule.execute()
    values=kwargs['values']
    logger.info("SIGNALS: The device "+ deviceName+" responded OK to the datagram " + str(datagramID)+" with values= "+str(values))
    
def Device_datagram_exception_handler(sender, **kwargs):
    deviceName=kwargs['DeviceName']
    datagramID=kwargs['DatagramId']
    HTMLCode=kwargs['HTMLCode']
    logger.error("SIGNALS: The device "+ deviceName+" responded to the datagram " + str(datagramID)+" with the code "+str(HTMLCode))
    
def Device_datagram_timeout_handler(sender, **kwargs):
    deviceIP=kwargs['DeviceIP']
    deviceName=kwargs['DeviceName']
    datagramID=kwargs['DatagramId']
    logger.warning ("SIGNALS: The device "+ deviceName+" at "+ deviceIP +" did not respond to the datagram " + str(datagramID))
    
def Device_datagram_format_error_handler(sender, **kwargs):
    deviceName=kwargs['DeviceName']
    datagramID=kwargs['DatagramId']
    values=kwargs['values']
    logger.warning("SIGNALS: The device "+ deviceName+" responded with a wrong format to the datagram " + str(datagramID)+" with values= "+str(values))
    
def DeviceName_changed_handler(sender,**kwargs):
    OLDdeviceName=kwargs['OldDeviceName']
    NEWdeviceName=kwargs['NewDeviceName']
    logger.info("SIGNALS: Ha cambiado el nombre del dispositivo " +OLDdeviceName+". Ahora se llama " + NEWdeviceName)
    applicationDBs=Devices.BBDD.DIY4dot0_Databases(devicesDBPath=Devices.GlobalVars.DEVICES_DB_PATH,registerDBPath=Devices.GlobalVars.REGISTERS_DB_PATH,
                                      configXMLPath=Devices.GlobalVars.XML_CONFFILE_PATH)   
    applicationDBs.rename_DeviceRegister_tables(OldDeviceName=OLDdeviceName,NewDeviceName=NEWdeviceName)

def Toggle_DeviceStatus_handler(sender,**kwargs):
    logger.info("SIGNALS: Enters Toggle_DeviceStatus_handler.")
    devicename=kwargs['DeviceName']
    Devices.Requests.toggle_requests(DeviceName=devicename)
    logger.info("SIGNALS: Ha cambiado el estado del dispositivo " +devicename+".")


    