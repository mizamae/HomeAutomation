from django.db import models

class EventmodelManager(models.Manager):
    def define_Event(self, DeviceName,DatagramId,variable_pos,boolean_expression,label):
        Ev = self.create(DeviceName=DeviceName,DatagramId=DatagramId,variable_pos=variable_pos,boolean_expression=boolean_expression,label=label)
        Ev.save()
    
class Eventmodel(models.Model):
    DIRECTION_CHOICES=(
        ('OUT','Output'),
        ('IN','Input'),
    )
    VALUE_CHOICES=(
        (0,'LOW'),
        (1,'HIGH'),
    )
    DeviceName = models.CharField(max_length=50)
    DatagramId = models.CharField(max_length=50)
    variable_pos = models.IntegerField()
    boolean_expression = models.CharField(max_length=50)
    label = models.CharField(max_length=50)
    
    objects = EventmodelManager()
    
    def __str__(self):
        return self.label
