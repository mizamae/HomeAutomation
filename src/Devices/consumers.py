import os
from channels.generic.websockets import WebsocketDemultiplexer,JsonWebsocketConsumer
import Devices.consumers 
from Devices.models import DeviceModelBinding as DeviceBinding
from .models import DeviceModel,DatagramModel
import Devices.signals

import logging
logger = logging.getLogger("project")

class DeviceModel_updater(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        process=os.getpid()
        logger.info("WS: Websocket request on process " + str(process))
        DV=DeviceModel.objects.get(DeviceName=content['data']["DeviceName"])
        #Devices.signals.Toggle_DeviceStatus.send(sender=None,Device=DV)
        DV.togglePolling()

class DeviceModel_delete(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        #logger.info("DeviceModel_delete original_message" + ":"+ str(content['data']))
        DV=DeviceModel.objects.get(DeviceName=content['data']["DeviceName"])
        DV.delete()

class DeviceModel_query(JsonWebsocketConsumer):
    def connect(self, message, **kwargs):
        pass
    
    def disconnect(self, message, **kwargs):
        pass
        
    def receive(self, content, multiplexer, **kwargs):
        DV=DeviceModel.objects.get(pk=content['pk'])
        
        if DV.Type.Connection=='REMOTE':
            import Devices.HTTP_client
            DGs=DatagramModel.objects.filter(DeviceType=DV.Type)
            DeviceCode=DV.DeviceCode
            deviceIP=DV.DeviceIP
            HTTPrequest=Devices.HTTP_client.HTTP_requests(server='http://'+deviceIP) 
            #data=[]
            #missing handling of several DGs per device
            for DG in DGs:
                data=HTTPrequest.request_datagram(DeviceCode=DeviceCode,DatagramId=DG.Identifier,writeToDB=False)
        elif (DV.Type.Connection=='LOCAL' or DV.Type.Connection=='MEMORY'):
            import Devices.callbacks
            data = getattr(Devices.callbacks, DV.Type.Code)(DV).query_sensor()
        DeviceName=DV.DeviceName
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



