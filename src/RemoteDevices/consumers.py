from channels.generic.websockets import WebsocketDemultiplexer,JsonWebsocketConsumer
import RemoteDevices.signals
from .models import DeviceModel

import logging
logger = logging.getLogger("project")

class DeviceModel_updater(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        #logger.info("DeviceModel_updater original_message" + ":"+ str(content['data']))
        RemoteDevices.signals.Toggle_DeviceStatus.send(sender="Stream", DeviceName=content['data']["DeviceName"])

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
        DeviceCode=DV.DeviceCode
        deviceIP=DV.DeviceIP
        import RemoteDevices.HTTP_client
        HTTPrequest=RemoteDevices.HTTP_client.HTTP_requests(server='http://'+deviceIP)    
        data=HTTPrequest.request_datagram(DeviceCode=DeviceCode,DatagramId="powers",writeToDB=False)
        multiplexer.send({"action":"query","DeviceName":devicename,"data":data})
        logger.info('Power: ' + str(data[1]))



