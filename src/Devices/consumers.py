from channels.generic.websockets import WebsocketDemultiplexer,JsonWebsocketConsumer
import RemoteDevices.consumers 
from RemoteDevices.models import DeviceModelBinding as RemoteDeviceBinding
import LocalDevices.consumers 
from LocalDevices.models import DeviceModelBinding as LocalDeviceBinding
import logging
logger = logging.getLogger("project")

        
class DeviceModel_consumers(WebsocketDemultiplexer):
    consumers = {
        "RDevice_params": RemoteDeviceBinding.consumer,
        "RDevice_update": RemoteDevices.consumers.DeviceModel_updater,
        "RDevice_delete": RemoteDevices.consumers.DeviceModel_delete,
        "RDevice_query": RemoteDevices.consumers.DeviceModel_query,
        "LDevice_params": LocalDeviceBinding.consumer,
        "LDevice_update": LocalDevices.consumers.DeviceModel_updater,
        "LDevice_delete": LocalDevices.consumers.DeviceModel_delete,
        "LDevice_query": LocalDevices.consumers.DeviceModel_query,
    }

    def connection_groups(self):
        return ["Device-models",]



