from channels import Group
from channels.generic.websockets import WebsocketDemultiplexer,JsonWebsocketConsumer
from .models import Events,EventsBinding

import logging
logger = logging.getLogger("project")

def ws_add_events(message):
    Group("Event-values").add(message.reply_channel)

def ws_disconnect_events(message):
    Group("Event-values").discard(message.reply_channel)
    
def PublishEvent(Severity,Code,Text,Persistent=False):
    import json
    from tzlocal import get_localzone
    from django.utils import timezone
    from utils.dataMangling import localizeTimestamp
    local_tz=get_localzone()
    Timestamp=timezone.now()
    localdate = localizeTimestamp(Timestamp.replace(tzinfo=None))
    if Persistent:
        EVT=Events(Timestamp=Timestamp,Severity=Severity,Code=Code,Text=Text)
        EVT.store2DB()
    else:
        Group('Event-values').send({'text':json.dumps({'Timestamp': localdate.strftime("%d %B %Y %H:%M:%S"),'Severity':Severity,'Text':Text,'Code':Code})},immediately=True)

class Events_updater(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        EVT=Events.objects.get(pk=int(content['pk']))
        EVT.delete()
        
    @classmethod
    def group_names(cls, *args, **kwargs):
        return ["Event-values",]

class Events_delete(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        EVT=Events.objects.get(pk=int(content['pk']))
        EVT.delete()
        pass

class Event_consumers(WebsocketDemultiplexer):
    consumers = {
        "Event_critical": EventsBinding.consumer,
        "Event_ack": Events_updater,
        "Event_delete": Events_delete,
    }

    def connection_groups(self):
        return ["Event-values",]        