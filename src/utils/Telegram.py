import os
import telepot
import logging
logger = logging.getLogger("project")

import environ
env = environ.Env()
from django.core.cache import cache
from DevicesAPP.constants import ENVIRON_FILE

if os.path.exists(ENVIRON_FILE):
    environ.Env.read_env(str(ENVIRON_FILE))

TELEGRAM_BOT_TOKEN = env('TELEGRAM_TOKEN')
TELEGRAM_CHNID_VAR='TELEGRAM_CHANNEL_ID'

class TelegramManager(object):
    def __init__(self):
        #logger.info('Bot TOKEN: ' + str(TELEGRAM_BOT_TOKEN))
        self.bot = telepot.Bot(TELEGRAM_BOT_TOKEN)
        self.chatID=TelegramManager.getChatID()
        #logger.info('ChatID: ' + str(self.chatID))
        if self.chatID==None:
            response = self.bot.getUpdates()
            #logger.info('Bot response: ' + str(response))
            if response!=[]:
                self.chatID=response[0]['channel_post']['chat']['id']
            else:
                self.chatID=None
        if self.chatID!=None:
            cache.set(TELEGRAM_CHNID_VAR, self.chatID,None)
            from MainAPP.models import SiteSettings
            SETTINGS=SiteSettings.load()
            SETTINGS.set_TELEGRAM_CHATID(value=self.chatID)
    
    @staticmethod
    def getChatID():
        chatID=cache.get(TELEGRAM_CHNID_VAR)
        if chatID==None:
            from MainAPP.models import SiteSettings
            SETTINGS=SiteSettings.load()
            chatID=getattr(SETTINGS,'TELEGRAM_CHATID')
            if chatID.strip()=='':
                chatID=None
        return chatID
        
    
    def sendMessage(self,text):
        if self.chatID!=None:
            self.bot.sendMessage(self.chatID, text)
        else:
            logger.error('TELEBOT: There are no messages in the chat. The bot needs at least one message to get the chatID')