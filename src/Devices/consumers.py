from channels.generic.websockets import WebsocketDemultiplexer,JsonWebsocketConsumer
import Devices.consumers 
from Devices.models import DeviceModelBinding as DeviceBinding
from .models import DeviceModel
import Devices.signals

import logging
logger = logging.getLogger("project")

class DeviceModel_updater(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        DV=DeviceModel.objects.get(DeviceName=content['data']["DeviceName"])
        Devices.signals.Toggle_DeviceStatus.send(sender="Stream", Device=DV)

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
        DV=DeviceModel.objects.get(pk=content['pk'])
        
        if DV.Type.Connection=='REMOTE':
            import Devices.HTTP_client
            DeviceCode=DV.DeviceCode
            deviceIP=DV.DeviceIP
            HTTPrequest=Devices.HTTP_client.HTTP_requests(server='http://'+deviceIP)    
            data=HTTPrequest.request_datagram(DeviceCode=DeviceCode,DatagramId="powers",writeToDB=False)
            DeviceName=DV.DeviceName
        elif DV.Type.Connection=='LOCAL':
            import Devices.callbacks
            data = getattr(Devices.callbacks, DV.Type.Code)(DV).query_sensor()
            DeviceName=DV.DeviceName
        logger.info("Sending back : " + str(data))
        multiplexer.send({"action":"query","DeviceName":DeviceName,"data":data})
        
class DeviceModel_consumers(WebsocketDemultiplexer):
    consumers = {
        "Device_params": DeviceBinding.consumer,
        "Device_update": DeviceModel_updater,
        "Device_delete": DeviceModel_delete,
        "Device_query": DeviceModel_query,

    }

    def connection_groups(self):
        return ["Device-models",]



