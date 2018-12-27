import os
from EventsAPP.consumers import PublishEvent
from django.utils.translation import ugettext_lazy as _

import logging
logger = logging.getLogger("project")

    
class WATCHDOG(object):
    
    Timer=None
    
    def __init__(self,name,interval,cachevar=None):
        self.name=name
        self.interval=interval
        self.cachevar=cachevar
        self.init_thread()
        
    def init_thread(self):
        from utils.asynchronous_tasks import BackgroundTimer
        if self.cachevar!=None:
            callable=self.cache_based
        self.Timer=BackgroundTimer(callable=callable,threadName=self.name,interval=self.interval,
                                    callablekwargs={'WATCHDOG_VAR':self.cachevar},repeat=True,triggered=False)
    
    def pause(self):
        if self.Timer.thread!=None:
            self.Timer.thread.pause()
    
    def resume(self):
        if self.Timer.thread!=None:
            self.Timer.thread.resume()
                    
    def kill(self):
        if self.Timer.thread!=None:
            self.Timer.thread.kill()
        self.Timer=None
        logger.error('Watchdog: Killed the thread')
    
    def cache_based(self,WATCHDOG_VAR):
        from django.core.cache import cache
        value=cache.get(WATCHDOG_VAR)
        Restart=False
        if value==None:
            logger.error('Watchdog: Cache value of '+WATCHDOG_VAR+' was None')
            value=True
            value_ant=True
        else:
            value_ant=cache.get(WATCHDOG_VAR+"_ant")
            
        cache.set(WATCHDOG_VAR+"_ant", value, self.interval*3)
        if value==value_ant:
            logger.error('Watchdog: Cache values of '+WATCHDOG_VAR+' coincide')
            fails=cache.get(WATCHDOG_VAR+"_FAILS") # number of consecutive failures
            if fails==None:
                fails=0
            cache.set(WATCHDOG_VAR+"_FAILS", fails+1, self.interval*10)
            if fails>=3:
                Restart=True
        else:
            cache.set(WATCHDOG_VAR+"_FAILS", 0, self.interval*10)
                
        if Restart:
            import os
            PublishEvent(Severity=10,Text=_("Devices polling watchdog forced a reset"),Persistent=True,Code='WatchDog')
            os.system("sudo systemctl restart gunicorn")    