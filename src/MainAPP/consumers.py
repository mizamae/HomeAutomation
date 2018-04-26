from channels.generic.websockets import WebsocketDemultiplexer,JsonWebsocketConsumer
from django.utils import timezone

from EventsAPP.consumers import PublishEvent

import logging
logger = logging.getLogger("project")

def ws_message(message):
    # ASGI WebSocket packet-received and send-packet message types
    # both have a "text" key for their textual data.
    print(message.content['text'])

class system_datetime_query(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        now = timezone.now().replace(microsecond=0)
        multiplexer.send({"action":"query_datetime",
                          "date":now.strftime('%d/%m/%Y'),
                          "time":now.strftime('%H:%M'),
                          })

class system_datetime_reset(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        from utils.NTPServer import restart
        restart()
        PublishEvent(Severity=2,Text=_("NTP server restarted"),Persistent=True,Code='MainAPP0')
        
class System_consumers(WebsocketDemultiplexer):
    consumers = {
        "datetime_query": system_datetime_query,
        "datetime_reset": system_datetime_reset,
    }

    def connection_groups(self):
        return ["System",]
        

def ws_add_avar(message):
    Group("AVAR-values").add(message.reply_channel)

def ws_disconnect_avar(message):
    Group("AVAR-values").discard(message.reply_channel)
    
class avar_update(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        from .models import AutomationVariables
        pk=content['pk']
        newValue=content['data']['newValue']
        AVAR=AutomationVariables.objects.get(pk=pk)
        AVAR.toggle(newValue=newValue)
        
    @classmethod
    def group_names(cls, *args, **kwargs):
        return ["AVAR-values",]
        
   
class AVAR_consumers(WebsocketDemultiplexer):
    consumers = {
        'AVAR_modify':avar_update,
        }

    def connection_groups(self):
        return ["AVAR-values",]