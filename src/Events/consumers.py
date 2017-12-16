from channels import Group
from channels.generic.websockets import WebsocketDemultiplexer,JsonWebsocketConsumer
from .models import EventModel,EventModelBinding

import logging
logger = logging.getLogger("project")

def ws_add(message):
    Group("Event-values").add(message.reply_channel)

def ws_disconnect(message):
    Group("Event-values").discard(message.reply_channel)
    
def PublishEvent(Severity,Text,Persistent=False):
    import json
    from tzlocal import get_localzone
    from django.utils import timezone
    local_tz=get_localzone()
    Timestamp=timezone.now()
    localdate = local_tz.localize(Timestamp.replace(tzinfo=None))
    localdate=localdate+localdate.utcoffset()
    if Persistent:
        try:
            EVM=EventModel.objects.get(Text=Text)
            EVM.Timestamp=Timestamp
        except:
            EVM=EventModel(Timestamp=Timestamp,Severity=Severity,Text=Text)
        EVM.save()
    else:
        Group('Event-values').send({'text':json.dumps({'Timestamp': localdate.strftime("%d %B %Y %H:%M:%S"),'Severity':Severity,'Text':Text})},immediately=True)
                                            
class EventModel_updater(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        #logger.info("EventModel_updater original_message" + ":"+ str(content))
        try:
            EVT=EventModel.objects.get(pk=int(content['pk']))
            EVT.delete()
        except:
            pass
        
    @classmethod
    def group_names(cls, *args, **kwargs):
        return ["Event-values",]

class EventModel_delete(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        #logger.info("EventModel_delete original_message" + ":"+ str(content['data']))
        #logger(str(content['data']["DeviceName"]))
        pass

class Event_consumers(WebsocketDemultiplexer):
    consumers = {
        "Event_critical": EventModelBinding.consumer,
        "Event_ack": EventModel_updater,
        "Event_delete": EventModel_delete,
    }

    def connection_groups(self):
        return ["Event-values",]        