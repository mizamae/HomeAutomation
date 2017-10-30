from channels.generic.websockets import WebsocketDemultiplexer,JsonWebsocketConsumer

import logging
logger = logging.getLogger("project")

def ws_message(message):
    # ASGI WebSocket packet-received and send-packet message types
    # both have a "text" key for their textual data.
    print(message.content['text'])

class progress_updater_query(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        logger.info("progress_updater_query original_message" + ":"+ str(content['data']))
        
        multiplexer.send({"action":"query","DeviceName":'',"data":''})
        
class System_consumers(WebsocketDemultiplexer):
    consumers = {
        "task_progress_query": progress_updater_query,
    }

    def connection_groups(self):
        return ["System",]
        
