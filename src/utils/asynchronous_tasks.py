import threading
import time
import datetime

import logging
logger = logging.getLogger("project")

class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self,name,target, *args,**kwargs):
        super(StoppableThread, self).__init__(name=name,target=target, *args,**kwargs)
        self._stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.trigger_event = threading.Event()
        pass

    def trigger(self):
        self.trigger_event.set()
        
    def pause(self):
        self.pause_event.set()
        
    def resume(self):
        self.pause_event.clear()
        
    def kill(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()
    
class BackgroundTimer(object):
    
    thread=None
    
    def __init__(self, callable,threadName,interval=1,callablekwargs={},
                 repeat=False,triggered=False,lifeSpan=None,
                 onThreadInit=None,onInitkwargs={},log=False):
        """ Constructor
        :type interval: int
        :param interval: Check interval, in seconds
        """
        self.interval = interval
        self.log=log
        if hasattr(callable, "__call__"):
            self.callable=callable
        else:
            self.callable=self._dummycallable
            
        self.callablekwargs=callablekwargs
        self.onInitkwargs=onInitkwargs
        self.threadName=threadName
        self.initiatedOn=datetime.datetime.now()
        self.lifeSpan=lifeSpan
        self.onThreadInit=onThreadInit
        
        exists=self.isAlive()
        if not exists: 
            self.initThread(repeat=repeat,triggered=triggered)
            time.sleep(3)   # to leave time for the thread to properly initiate
            
    def initThread(self,repeat,triggered):
        if not repeat:
            target=self.run
        elif triggered:
            target=self.runTriggered
        else:
            target=self.runForever
            
        self.thread = StoppableThread(name=self.threadName,target=target, args=())
        self.thread.daemon = True                            # Daemonize thread
        self.start()                                  # Start the execution
            
    def kill(self):
        try:
            self.thread.kill()
            logger.info("A thread with the ident " + str(self.thread.ident) + " has been killed")
        except:
            pass
    
    def checkSurvival(self):
        if self.lifeSpan!=None and (datetime.datetime.now()-self.initiatedOn>datetime.timedelta(seconds=self.lifeSpan)):
            self.kill()
        
    def start(self):
        self.thread.start()
    
    def pause(self):
        self.thread.pause()
    
    def resume(self):
        self.thread.resume()
    
    def trigger(self):
        self.thread.trigger()
        
    def isAlive(self):
        exists=False
        for t in threading.enumerate():
            if t.name==self.threadName:
                self.thread=t
                logger.info("A thread with the name " + self.threadName + " and ident " + str(self.thread.ident) +" exists")
                exists=True
                break
        return exists
    
    def _dummycallable(self):
        pass
    
    def run(self):
        """ Method that runs only once """
        if hasattr(self.onThreadInit, "__call__"):
            self.onThreadInit(**self.onInitkwargs)
            
        time.sleep(self.interval)
        self.callable(**self.callablekwargs)
        if self.log:
            logger.info("Executed function " + str(self.callable) + " with kwargs " + str(self.callablekwargs))
        self.thread=None
    
    def runForever(self):
        """ Method that runs forever """
        if hasattr(self.onThreadInit, "__call__"):
            self.onThreadInit(**self.onInitkwargs)
            
        while not self.thread._stop_event.isSet():
            time.sleep(self.interval)
            if not self.thread.pause_event.isSet():
                self.callable(**self.callablekwargs)
            self.checkSurvival()
        self.thread=None
                
    def runTriggered(self):
        """ Method that runs forever """
        if hasattr(self.onThreadInit, "__call__"):
            self.onThreadInit(**self.onInitkwargs)
            
        while not self.thread._stop_event.isSet():
            if self.thread.trigger_event.isSet():
                self.thread.trigger_event.clear()
                self.callable(**self.callablekwargs)
            self.checkSurvival()
        self.thread=None