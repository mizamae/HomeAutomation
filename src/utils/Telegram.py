import os
import telepot
import json
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
    instructions=[{'id':'command','text':_('Commands')},]
    
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
            msg=str(_('SYSTEM RESET\n Available instructions:\n'))
            self.bot.sendMessage(self.chatID,msg)
            
            inlinesCMD=[]
            for instruction in TelegramManager.instructions:
                 inlinesCMD.append([InlineKeyboardButton(text=str(instruction['text']), callback_data=json.dumps({'id':instruction['id'],'payload':None,'pk':None}))])
            keyboard = InlineKeyboardMarkup(inline_keyboard=inlinesCMD)
            self.bot.sendMessage(self.chatID, str(_('Menu')), reply_markup=keyboard)
                
        MessageLoop(self.bot, {'chat': self.on_chat_message,
                  'callback_query': self.on_callback_query}).run_as_thread()
    
    def on_chat_message(self,msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if msg!=[]:
            self.chatID=msg['chat']['id']
            receivedMSG=msg['text']
        else:
            receivedMSG=None
        
        if 'hola' in receivedMSG:
            self.bot.sendMessage(chat_id, str(_('Hola caracola!')))
        else:
            self.bot.sendMessage(chat_id, str(_('Sorry but I do not understand you!')))
    
    def on_callback_query(self,msg):
        from DevicesAPP.models import Devices,DeviceCommands
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        
        logger.info('Callback Query:', query_id, from_id, query_data)
        query_data=json.loads(query_data)
        if query_data['id']==TelegramManager.instructions[0]['id']: # Ask for commands list            
            DVs=Devices.objects.all()
            inlinesCMD=[]
            for DV in DVs:
                CMDs=DV.getDeviceCommands()
                for CMD in CMDs:
                    inlinesCMD.append([InlineKeyboardButton(text=str(DV)+"\n"+str(CMD), callback_data=json.dumps({'id':None,'payload':None,'DVpk':DV.pk,'CMDpk':CMD.pk}))])
            keyboard = InlineKeyboardMarkup(inline_keyboard=inlinesCMD)
            
            if len(inlinesCMD)>0:
                self.bot.sendMessage(self.chatID, str(_('Select the command to execute')), reply_markup=keyboard)
            else:
                self.bot.sendMessage(self.chatID, str(_('No available commands to execute')))           
            self.bot.answerCallbackQuery(query_id, text=str(_('Got it')))
        elif query_data['DVpk']!=None and query_data['CMDpk']!=None:
            DV=Devices.objects.get(pk=query_data['DVpk'])
            CMD=DeviceCommands.objects.get(pk=query_data['CMDpk'])
            data=DV.requestOrders(serverIP=DV.IP,order=CMD.Identifier,payload=CMD.getPayload(),timeout=1)
            if data[0]==200:
                self.bot.answerCallbackQuery(query_id, text=str(_('Got it, executed '))+str(CMD))
            else:
                self.bot.answerCallbackQuery(query_id, text=str(_('Error executing '))+str(CMD)+": "+str(data[1]))
        else:
            self.bot.answerCallbackQuery(query_id, text=str(_('Got it')))
        
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