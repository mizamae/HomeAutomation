from channels import Group
from channels.generic.websockets import WebsocketDemultiplexer,JsonWebsocketConsumer
from .models import Events,EventsBinding

import logging
logger = logging.getLogger("project")

def ws_add_events(message):
    Group("Event-values").add(message.reply_channel)

def ws_disconnect_events(message):
    Group("Event-values").discard(message.reply_channel)
    
def PublishEvent(Severity,Code,Text,Persistent=False,Webpush=False):
    import json
    from tzlocal import get_localzone
    from django.utils import timezone
    from utils.dataMangling import localizeTimestamp
    local_tz=get_localzone()
    Timestamp=timezone.now()
    localdate = localizeTimestamp(Timestamp.replace(tzinfo=None))
    if Webpush:
        try:
            from utils.web_notifications import NotificationManager
            NotificationManager.send_web_push(users=NotificationManager.getUsers(), title='DIY4dot0 - Events',
                                              tag='notifications-'+Code,message_body=Text,
                                              url='http://mizamae2.ddns.net:8075')
            from utils.Telegram import TelegramManager
            TelegramManager().sendMessage(text=Text)
        except Exception as exc:
            pass
        
    if Persistent:
        EVT=Events(Timestamp=Timestamp,Severity=Severity,Code=Code,Text=Text)
        EVT.store2DB()
    else:
        Group('Event-values').send({'text':json.dumps({'Timestamp': localdate.strftime("%d %B %Y %H:%M:%S"),'Severity':Severity,'Text':Text,'Code':Code})},immediately=True)

class Events_updater(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        try:
            EVT=Events.objects.get(pk=int(content['pk']))
            EVT.delete()
        except:
            pass
        
    @classmethod
    def group_names(cls, *args, **kwargs):
        return ["Event-values",]

class Events_delete(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        try:
            EVT=Events.objects.get(pk=int(content['pk']))
            EVT.delete()
        except:
            pass

class Event_consumers(WebsocketDemultiplexer):
    consumers = {
        "Event_critical": EventsBinding.consumer,
        "Event_ack": Events_updater,
        "Event_delete": Events_delete,
    }

    def connection_groups(self):
        return ["Event-values",]        