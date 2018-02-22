from channels import Group
from channels.generic.websockets import WebsocketDemultiplexer,JsonWebsocketConsumer



import logging
logger = logging.getLogger("project")

def ws_add_profiles(message):
    Group("Profiles-values").add(message.reply_channel)

def ws_disconnect_profiles(message):
    Group("Profiles-values").discard(message.reply_channel)
    
class track_update(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        pass
        
    @classmethod
    def group_names(cls, *args, **kwargs):
        return ["Profiles-values",]
        
   
class userTracks_consumers(WebsocketDemultiplexer):
    consumers = {
        "Profiles_values": track_update,}

    def connection_groups(self):
        return ["Profiles-values",]
    