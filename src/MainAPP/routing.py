from channels import route_class
from channels.routing import route
from .consumers import ws_message
from DevicesAPP.consumers import DevicesAPP_consumers 
from MainAPP.consumers import System_consumers,AVAR_consumers,ws_add_avar,ws_disconnect_avar
from profiles.consumers import userTracks_consumers,ws_add_profiles,ws_disconnect_profiles
from EventsAPP.consumers import Event_consumers,ws_add_events,ws_disconnect_events

channel_routing = [
    route_class(DevicesAPP_consumers, path='^/stream/DevicesAPP/'),
    route_class(System_consumers, path='^/stream/System/'),
    route_class(AVAR_consumers, path='^/stream/MainAPP/avars/'),
    route("websocket.connect", ws_add_avar, path='^/stream/MainAPP/avars/'),
    route("websocket.disconnect", ws_disconnect_avar, path='^/stream/MainAPP/avars/'),
    route_class(userTracks_consumers, path='^/stream/UserTracking/'),
    route("websocket.connect", ws_add_profiles, path='^/stream/UserTracking/'),
    route("websocket.disconnect", ws_disconnect_profiles, path='^/stream/UserTracking/'),
    route_class(Event_consumers, path='^/stream/Events/'),
    route("websocket.connect", ws_add_events, path='^/stream/Events/'),
    route("websocket.disconnect", ws_disconnect_events, path='^/stream/Events/'),
]
