from channels.generic.websockets import WebsocketDemultiplexer,JsonWebsocketConsumer

from .models import IOmodelBinding
import Master_GPIOs

import logging
logger = logging.getLogger("project")

class GPIO_updater(JsonWebsocketConsumer):
    def receive(self, content, multiplexer, **kwargs):
        #logger.info("GPIO_updater original_message" + ":"+ str(content))
        Master_GPIOs.signals.OUT_toggle_request.send(sender="Stream", number=content["pk"])

class GPIO_consumers(WebsocketDemultiplexer):
    consumers = {
        "GPIO_values": IOmodelBinding.consumer,
        "GPIO_update": GPIO_updater,
    }

    def connection_groups(self):
        return ["GPIO-values",]



