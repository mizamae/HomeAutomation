import os
import logging
import utils.BBDD
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
logger = logging.getLogger("project")

def Device_datagram_reception_handler(sender, **kwargs):
    timestamp=kwargs['timestamp']
    DV=kwargs['Device']
    #DG=kwargs['Datagram']
    #values=kwargs['values']
    #logger.info("SIGNALS: The device "+ DV.DeviceName+" responded OK to the datagram with values= "+str(values))
    
def Device_datagram_exception_handler(sender, **kwargs):
    DV=kwargs['Device']
    #DG=kwargs['Datagram']
    Error=kwargs['Error']
    #print("SIGNALS: The device "+ DV.DeviceName+" responded to the datagram " + str(datagram.Identifier)+" with the code "+str(Error))
    #logger.error("SIGNALS: The device "+ DV.DeviceName+" responded to the datagram " + str(datagram.Identifier)+" with the code "+str(Error))
    
def Device_datagram_timeout_handler(sender, **kwargs):
    DV=kwargs['Device']
    #DG=kwargs['Datagram']
    #print("SIGNALS: The device "+ DV.DeviceName+" at "+ DV.DeviceIP +" did not respond to the datagram " + str(DG.Identifier))
    #logger.warning ("SIGNALS: The device "+ DV.DeviceName+" at "+ DV.DeviceIP +" did not respond to the datagram " + str(DG.Identifier))
    
def Device_datagram_format_error_handler(sender, **kwargs):
    DV=kwargs['Device']
    #DG=kwargs['Datagram']
    #values=kwargs['values']
    #print("SIGNALS: The device "+ DV.DeviceName+" responded with a wrong format to the datagram " + str(DG.Identifier)+" with values= "+str(values))
    #logger.warning("SIGNALS: The device "+ DV.DeviceName+" responded with a wrong format to the datagram " + str(DG.Identifier)+" with values= "+str(values))
    
def DeviceName_changed_handler(sender,**kwargs):
    OLDdeviceName=kwargs['OldDeviceName']
    NEWdeviceName=kwargs['NewDeviceName']
    print("SIGNALS: Ha cambiado el nombre del dispositivo " +OLDdeviceName+". Ahora se llama " + NEWdeviceName)


def Toggle_DeviceStatus_handler(sender,**kwargs):
    process=os.getpid()
    #logger.info("SIGNALS: Enters Toggle_DeviceStatus_handler.")
    DV=kwargs['Device']
    #DevicesAPP.Requests.update_requests(DV=DV)
    logger.info("SIGNALS: Ha cambiado el estado del dispositivo " +DV.DeviceName+" en el proceso "+str(process))


    