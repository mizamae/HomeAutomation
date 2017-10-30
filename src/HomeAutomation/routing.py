from channels import route_class
from channels.routing import route
from .consumers import ws_message
from Master_GPIOs.consumers import GPIO_consumers
from Devices.consumers import DeviceModel_consumers 
from HomeAutomation.consumers import System_consumers

channel_routing = [
    route_class(GPIO_consumers, path='^/stream/GPIOs/'),
    route_class(DeviceModel_consumers, path='^/stream/DeviceModels/'),
    route_class(System_consumers, path='^/stream/System/'),
]
