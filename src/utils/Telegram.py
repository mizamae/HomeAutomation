import os
import telepot
import logging
logger = logging.getLogger("project")

import environ
env = environ.Env()
from DevicesAPP.constants import ENVIRON_FILE

if os.path.exists(ENVIRON_FILE):
    environ.Env.read_env(str(ENVIRON_FILE))

TELEGRAM_BOT_TOKEN = env('TELEGRAM_TOKEN')

class TelegramManager(object):
    def __init__(self):
        self.bot = telepot.Bot(TELEGRAM_BOT_TOKEN)
        response = self.bot.getUpdates()
        if response!=[]:
            self.chatID=response[0]['channel_post']['chat']['id']
        else:
            self.chatID=None
        
    def sendMessage(self,text):
        if self.chatID!=None:
            self.bot.sendMessage(self.chatID, text)
        else:
            logger.error('TELEBOT: There are no messages in the chat. The bot needs at least one message to get the chatID')