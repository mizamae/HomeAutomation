from apscheduler.schedulers.background import BackgroundScheduler
import apscheduler.events as events

class PollingScheduler(BackgroundScheduler):
    def __init__(self,jobstoreUrl,*args,**kwargs):
        super().__init__(*args,**kwargs)
        super().add_jobstore('sqlalchemy', url=jobstoreUrl)
        super().add_listener(callback=self.my_listener, mask=events.EVENT_JOB_EXECUTED | events.EVENT_JOB_ERROR)
    
    def run(self):
        try:
            self.start()
        except BaseException as e:
            logger.info('Exception APS: ' + str(e))
            
    def stop(self):
        self.shutdown()
        
    def remove_job(self,jobId):
        initialState=self.running
        if initialState==False:
            self.run()
        super().remove_job(jobId)
        if initialState==False:
            self.stop()
            
    def getJobsInStore(self):
        initialState=self.running
        if initialState==False:
            self.run()
        JOBs=self.get_jobs()
        if initialState==False:
            self.stop()
        return JOBs
    
    def getJobInStore(self,jobId):
        initialState=self.running
        if initialState==False:
            self.run()
        JOB=self.get_job(job_id=jobId)
        if initialState==False:
            self.stop()
        return JOB
    
    def my_listener(self,event):
        if event.exception:
            try:
                text='The scheduled task '+event.job_id+' reported an error: ' + str(event.traceback) 
                logger.info("APS: " + str(event.traceback))
            except:
                text='Error on scheduler: ' + str(event.exception)
                logger.info("APS: " + str(event.exception))
            PublishEvent(Severity=4,Text=text,Persistent=True)
        else:
            pass