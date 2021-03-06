from channels.generic.websockets import WebsocketDemultiplexer,JsonWebsocketConsumer
from django.utils import timezone

from EventsAPP.consumers import PublishEvent

import logging
logger = logging.getLogger("project")

def ws_message(message):
    # ASGI WebSocket packet-received and send-packet message types
    # both have a "text" key for their textual data.
    print(message.content['text'])

class system_status(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        action=content['action']
        if action=='loading_status':
            from django.core.cache import cache
            loading=cache.get(key='loading',default=False)
            multiplexer.send({"action":"loading_status",
                              "loading":loading,
                              })
        elif action=='query_datetime':
            now = timezone.now().replace(microsecond=0)
            multiplexer.send({"action":"query_datetime",
                              "date":now.strftime('%d/%m/%Y'),
                              "time":now.strftime('%H:%M'),
                              })
        elif action=='reset_datetime':
            from utils.NTPServer import restart
            restart()
            PublishEvent(Severity=2,Text="NTP server restarted",Persistent=True,Code='MainAPP0')
        
        
class System_consumers(WebsocketDemultiplexer):
    consumers = {
        "system_status": system_status,
    }

    def connection_groups(self):
        return ["System",]
        
def ws_add_avar(message):
    Group("AVAR-values").add(message.reply_channel)

def ws_disconnect_avar(message):
    Group("AVAR-values").discard(message.reply_channel)
    
class avar_update(JsonWebsocketConsumer):
    http_user = True
    
    def receive(self, content, multiplexer, **kwargs):
        action=content['action']
        
        if action=="toggle":
            from .models import AutomationVariables
            logger.debug('Received WS!!: ' + str(content))
            pk=content['pk']
            newValue=content['data']['newValue']
            #logger.debug(content['data']['overrideTime'])
            try:
                overrideTime=int(content['data']['overrideTime'])
            except:
                overrideTime=None
            AVAR=AutomationVariables.objects.get(pk=pk)
            AVAR.updateValue(newValue=newValue,overrideTime=overrideTime)
        elif action=="reorder":
            newOrder=list(map(int,content['data']['newOrder']))
            subsystem=str(content['data']['subsystem'])
            user=self.message.user
            user.profile.set_general_feature(key='AVAR_order_'+subsystem,value=newOrder)
            pass
        
    @classmethod
    def group_names(cls, *args, **kwargs):
        return ["AVAR-values",]
        
    
class AVAR_consumers(WebsocketDemultiplexer):
    consumers = {
        'AVAR_modify':avar_update,
        }

    def connection_groups(self):
        return ["AVAR-values",]