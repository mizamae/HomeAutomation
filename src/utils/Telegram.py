import os
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from django.utils.translation import ugettext_lazy as _

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
            
        if self.chatID!=None:
            cache.set(TELEGRAM_CHNID_VAR, self.chatID,None)
            from MainAPP.models import SiteSettings
            SETTINGS=SiteSettings.load()
            SETTINGS.set_TELEGRAM_CHATID(value=self.chatID)
    
    def initChatLoop(self):
        if self.chatID!=None:
            self.bot.sendMessage(self.chatID, 
                                 str(_('SYSTEM RESET\n Available instructions:\n    - "Commands"\n    - "Others"')))

        MessageLoop(self.bot, {'chat': self.on_chat_message,
                  'callback_query': self.on_callback_query}).run_as_thread()
    
    def on_chat_message(self,msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if msg!=[]:
            self.chatID=msg['chat']['id']
            receivedMSG=msg['text']
        else:
            receivedMSG=None
        
        if receivedMSG!=None:
            if receivedMSG==_('Commands'):
                from DevicesAPP.models import DeviceCommands
                CMDs=DeviceCommands.objects.all()
                inlinesCMD=[]
                for CMD in CMDs:
                     inlinesCMD.append([InlineKeyboardButton(text=str(CMD), callback_data={'identifier':CMD.Identifier,'payload':CMD.getPayload()})])
                keyboard = InlineKeyboardMarkup(inline_keyboard=inlinesCMD)
                
                if len(inlinesCMD)>0:
                    self.bot.sendMessage(chat_id, str(_('Select the command to execute')), reply_markup=keyboard)
                else:
                    self.bot.sendMessage(chat_id, str(_('No available commands to execute')))
    
    def on_callback_query(self,msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        logger.info('Callback Query:', query_id, from_id, query_data)
    
        self.bot.answerCallbackQuery(query_id, text=str(_('Got it, executed '))+query_data['identifier']+str(_(' with payload: '))+str(query_data['payload']))
    
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