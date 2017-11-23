from django.db import models
from channels.binding.websockets import WebsocketBinding
from django.dispatch import receiver
from django.db.models.signals import post_save,post_delete,pre_delete

class EventModel(models.Model):
    
    Timestamp = models.DateTimeField(auto_now_add=True)
    Severity = models.PositiveSmallIntegerField(default=0)
    Text = models.CharField(max_length=150)
    IsRead = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        try:
            EVT=EventModel.objects.get(Text=self.Text)
        except:
            EVT=None
        if EVT==None:
            super(EventModel, self).save(*args, **kwargs)
        else:
            EVT.Timestamp=self.Timestamp
            EVT.save()
        
    def __str__(self):
        return self.Text

@receiver(post_save, sender=EventModel, dispatch_uid="update_EventModel")
def update_EventModel(sender, instance, update_fields,**kwargs):
        
    if kwargs['created']:   # new instance is created
        pass
    else:
        if instance.IsRead:
            instance.delete()
            
        
class EventModelBinding(WebsocketBinding):

    model = EventModel
    stream = "Event_critical"
    fields = ["Timestamp","Severity","Text","IsRead"]

    @classmethod
    def group_names(cls, *args, **kwargs):
        return ["Event-values",]

    def has_permission(self, user, action, pk):
        return True