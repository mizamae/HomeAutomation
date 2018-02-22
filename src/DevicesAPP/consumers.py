import os
from channels.generic.websockets import WebsocketDemultiplexer,JsonWebsocketConsumer
from .models import Devices,Datagrams,DevicesBinding,MasterGPIOs,MasterGPIOsBinding
from . import signals
from .constants import LOCAL_CONNECTION,REMOTE_TCP_CONNECTION,MEMORY_CONNECTION,DG_SYNCHRONOUS
import logging
logger = logging.getLogger("project")

class Devices_updater(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        process=os.getpid()
        #logger.info("WS: Websocket request on process " + str(process))
        DV=Devices.objects.get(Name=content['data']["Name"])
        #Devices.signals.Toggle_DeviceStatus.send(sender=None,Device=DV)
        DV.togglePolling()

class Devices_delete(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        #logger.info("Devices_delete original_message" + ":"+ str(content['data']))
        DV=Devices.objects.get(Name=content['data']["Name"])
        DV.delete()

class Devices_query(JsonWebsocketConsumer):
    def connect(self, message, **kwargs):
        pass
    
    def disconnect(self, message, **kwargs):
        pass
        
    def receive(self, content, multiplexer, **kwargs):
        DV=Devices.objects.get(pk=int(content['data']['DevicePK']))
        Labels=DV.get
        if DV.Type.Connection==REMOTE_TCP_CONNECTION:
            DGs=Datagrams.objects.filter(DeviceType=DV.Type).filter(Type=DG_SYNCHRONOUS)
            for DG in DGs:
                status=DV.request_datagram(DatagramId=DG.Identifier,writeToDB=False)
                data=status['values']
                multiplexer.send({"action":"query","DeviceName":DV.Name,"Datagram":DG.Identifier,"data":data})
        elif (DV.Type.Connection==LOCAL_CONNECTION or DV.Type.Connection==MEMORY_CONNECTION):
            import DevicesAPP.callbacks
            data = getattr(Devices.callbacks, DV.Type.Code)(DV).query_sensor()
            multiplexer.send({"action":"query","DeviceName":DV.Name,"data":data})

class GPIO_updater(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        logger.info("Received signal to toggle output " + str(number) + " on the process " + str(os.getpid()))
        # toggle gpio number
        IO=MasterGPIOs.objects.get(Pin=content["pk"])
        IO.toggle()
    
class DevicesAPP_consumers(WebsocketDemultiplexer):
    consumers = {
        "Device_params": DevicesBinding.consumer,
        "Device_update": Devices_updater,
        "Device_delete": Devices_delete,
        "Device_query": Devices_query,
        "GPIO_values": MasterGPIOsBinding.consumer,
        "GPIO_update": GPIO_updater,
    }

    def connection_groups(self):
        return ["Device-models","GPIO-models"]



