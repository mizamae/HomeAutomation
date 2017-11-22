from channels import route_class
from channels.routing import route
from .consumers import ws_message
from Master_GPIOs.consumers import GPIO_consumers
from Devices.consumers import DeviceModel_consumers 
from HomeAutomation.consumers import System_consumers
from profiles.consumers import userTracks_consumers,ws_add,ws_disconnect
from Events.consumers import Event_consumers,ws_add,ws_disconnect

channel_routing = [
    route_class(GPIO_consumers, path='^/stream/GPIOs/'),
    route_class(DeviceModel_consumers, path='^/stream/DeviceModels/'),
    route_class(System_consumers, path='^/stream/System/'),
    route_class(userTracks_consumers, path='^/stream/UserTracking/'),
    route("websocket.connect", ws_add, path='^/stream/UserTracking/'),
    route("websocket.disconnect", ws_disconnect, path='^/stream/UserTracking/'),
    route_class(Event_consumers, path='^/stream/Events/'),
    route("websocket.connect", ws_add, path='^/stream/Events/'),
    route("websocket.disconnect", ws_disconnect, path='^/stream/Events/'),
]
