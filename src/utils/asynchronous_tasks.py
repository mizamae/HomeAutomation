import threading
import time


class BackgroundTimer(object):

    def __init__(self, callable,threadName,interval=1,kwargs={},repeat=False):
        """ Constructor
        :type interval: int
        :param interval: Check interval, in seconds
        """
        self.interval = interval
        self.callable=callable
        self.kwargs=kwargs
        for t in threading.enumerate():
            if t.name==threadName:
                print("A thread with the name " + threadName + " exists")
        thread = threading.Thread(name=threadName,target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution
        
    def run(self):
        """ Method that runs forever """
        time.sleep(self.interval)
        self.callable(**self.kwargs)

