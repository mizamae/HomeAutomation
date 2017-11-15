from channels.generic.websockets import JsonWebsocketConsumer
import LocalDevices.signals
import LocalDevices.callbacks
from .models import DeviceModel

import logging
logger = logging.getLogger("project")

class DeviceModel_updater(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        LocalDevices.signals.Toggle_DeviceStatus.send(sender="Stream", DeviceName=content['data']["DeviceName"])

class DeviceModel_delete(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        #logger.info("DeviceModel_delete original_message" + ":"+ str(content['data']))
        device=DeviceModel.objects.get(DeviceName=content['data']["DeviceName"])
        device.delete()
        
class DeviceModel_query(JsonWebsocketConsumer):
    def connect(self, message, **kwargs):
        pass
    
    def disconnect(self, message, **kwargs):
        pass
        
    def receive(self, content, multiplexer, **kwargs):
        #logger.info("DeviceModel_query original_message" + ":"+ str(content['data']))
        devicename=content['data']["DeviceName"]
        DV=DeviceModel.objects.get(DeviceName=devicename)
        DeviceType=DV.Type.Code
        data = getattr(LocalDevices.callbacks, DeviceType)(DV).query_sensor()
        multiplexer.send({"action":"query","DeviceName":devicename,"data":data})
        #logger.info('Temperature: ' + str(data[1]))
        #logger.info('Dewpoint: ' + str(data[2]))



