from django.db import models
from channels.binding.websockets import WebsocketBinding
from django.dispatch import receiver
from django.db.models.signals import post_save,post_delete,pre_delete

class Events(models.Model):
    
    Timestamp = models.DateTimeField(auto_now_add=True)
    Severity = models.PositiveSmallIntegerField(default=0)
    Text = models.CharField(max_length=150)
    Code = models.CharField(max_length=50)
    IsRead = models.BooleanField(default=False)
    
    def store2DB(self):
        EVT=Events.checkIfExist(event=self)
        if EVT==None:
            super().save()
        else:
            EVT.Timestamp=self.Timestamp
            EVT.save()
    
    @classmethod
    def checkIfExist(cls,event):
        try:
            EVT=cls.objects.get(Code=event.Code)
            return EVT
        except:
            return None
        
        
    def __str__(self):
        return self.Text

@receiver(post_save, sender=Events, dispatch_uid="update_Events")
def update_Events(sender, instance, update_fields,**kwargs):
        
    if kwargs['created']:   # new instance is created
        pass
    else:
        if instance.IsRead:
            instance.delete()
            
        
class EventsBinding(WebsocketBinding):

    model = Events
    stream = "Event_critical"
    fields = ["Timestamp","Severity","Text","IsRead"]

    @classmethod
    def group_names(cls, *args, **kwargs):
        return ["Event-values",]

    def has_permission(self, user, action, pk):
        return True