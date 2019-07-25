import os
from channels.generic.websockets import WebsocketDemultiplexer,JsonWebsocketConsumer
from .models import Devices,Datagrams,DevicesBinding,MasterGPIOs,MasterGPIOsBinding,DeviceCommands
from . import signals
from .constants import LOCAL_CONNECTION,REMOTE_TCP_CONNECTION,REMOTE_RS485_CONNECTION,MEMORY_CONNECTION,DG_SYNCHRONOUS
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
        DV=Devices.objects.get(pk=int(content['pk']))
        if DV.DVT.Connection==REMOTE_TCP_CONNECTION:
            DGs=Datagrams.objects.filter(DVT=DV.DVT).filter(Type=DG_SYNCHRONOUS)
            for DG in DGs:
                status=DV.requestDatagram(DatagramId=DG.Identifier,writeToDB=False,resetOrder=False)
                data=status['values']
                multiplexer.send({"action":"query","DeviceName":DV.Name,"Datagram":DG.Identifier,"data":status})
        elif (DV.DVT.Connection==LOCAL_CONNECTION or DV.DVT.Connection==MEMORY_CONNECTION or DV.DVT.Connection==REMOTE_RS485_CONNECTION):
            import DevicesAPP.callbacks
            data = getattr(DevicesAPP.callbacks, DV.DVT.Code)(DV).query_sensor()
            multiplexer.send({"action":"query","DeviceName":DV.Name,"data":data})

class Devices_command(JsonWebsocketConsumer):
    def connect(self, message, **kwargs):
        pass
    
    def disconnect(self, message, **kwargs):
        pass
        
    def receive(self, content, multiplexer, **kwargs):
        logger.info('Received order to ' + str(content))
        CMD=DeviceCommands.objects.get(pk=int(content['pk']))
        #logger.info('Received order ' + str(CMD))
        DV=Devices.objects.get(pk=int(content['data']['devicePK']))
        #logger.info('Received order to ' + str(DV))
        data=DV.requestOrders(serverIP=DV.IP,order=CMD.Identifier,payload=CMD.getPayload(),timeout=1)
        multiplexer.send({"action":"command","DeviceName":DV.Name,"CMD":CMD.pk,"data":data})
        pass
        

class Device_pendingjob(JsonWebsocketConsumer):
    def connect(self, message, **kwargs):
        pass
    
    def disconnect(self, message, **kwargs):
        pass
        
    def receive(self, content, multiplexer, **kwargs):
        import datetime
        try:
            from .callbacks import PENDING_DB
            DV=Devices.objects.get(pk=int(content['pk']))           
            date=datetime.datetime.strptime(content['data']['date'], '%Y-%m-%d').date()
            action=content['action']
            if action=="add":
                DG=Datagrams.objects.get(pk=int(content['data']['DG_pk']))
                PENDING_DB.add_pending_job(DV=DV,datagramId=DG.Identifier,date=date)
                multiplexer.send({"action":"confirmed"})
            elif action=="execute":
                DG=Datagrams.objects.get(DVT=DV.DVT,Identifier=content['data']['DG_id'])
                import DevicesAPP.callbacks
                sender=getattr(DevicesAPP.callbacks, DV.DVT.Code)            
                PENDING_DB.execute_pending_jobs(sender=sender,DV=DV,dated=date,datagramID=DG.Identifier)
                multiplexer.send({"action":"confirmed"})
        except Exception as exc:
            multiplexer.send({"action":"not confirmed",'error':str(exc)})
    

class GPIO_updater(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        logger.info("Received signal to toggle output " + str(content["pk"]))
        # toggle gpio number
        IO=MasterGPIOs.objects.get(Pin=content["pk"])
        IO.toggle()
    
class DevicesAPP_consumers(WebsocketDemultiplexer):
    consumers = {
        "Device_params": DevicesBinding.consumer,
        "Device_update": Devices_updater,
        "Device_pendingjob": Device_pendingjob,
        "Device_delete": Devices_delete,
        "Device_query": Devices_query,
        "Device_command": Devices_command,
        "GPIO_values": MasterGPIOsBinding.consumer,
        "GPIO_update": GPIO_updater,
    }

    def connection_groups(self):
        return ["Device-models","GPIO-models"]



