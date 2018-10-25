import threading
import time
import datetime

class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self,name,target, args):
        super(StoppableThread, self).__init__(name=name,target=target, args=args)
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

    def __init__(self, callable,threadName,interval=1,callablekwargs={},
                 repeat=False,triggered=False,lifeSpan=None,
                 onThreadInit=None,onInitkwargs={}):
        """ Constructor
        :type interval: int
        :param interval: Check interval, in seconds
        """
        self.interval = interval
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
            time.sleep(1)   # to leave time for the thread to properly initiate
            
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
        self.thread.kill()
    
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
                #print("A thread with the name " + self.threadName + " exists")
                self.thread=t
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
    
    def runForever(self):
        """ Method that runs forever """
        if hasattr(self.onThreadInit, "__call__"):
            self.onThreadInit(**self.onInitkwargs)
            
        while not self.thread._stop_event.isSet():
            if not self.thread.pause_event.isSet():
                time.sleep(self.interval)
                self.callable(**self.callablekwargs)
            self.checkSurvival()
                
    def runTriggered(self):
        """ Method that runs forever """
        if hasattr(self.onThreadInit, "__call__"):
            self.onThreadInit(**self.onInitkwargs)
            
        while not self.thread._stop_event.isSet():
            if self.thread.trigger_event.isSet():
                self.thread.trigger_event.clear()
                self.callable(**self.callablekwargs)
            self.checkSurvival()