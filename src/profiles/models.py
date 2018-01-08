# coding: utf-8
from __future__ import unicode_literals
from django.utils.translation import ugettext as _
import uuid
from channels.binding.websockets import WebsocketBinding

from django.utils import timezone
from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.dispatch import receiver
from django.db.models.signals import post_save,post_delete,pre_delete
from channels import Group
from Events.consumers import PublishEvent

import logging

logger = logging.getLogger("project")

class BaseProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                primary_key=True)
    slug = models.UUIDField(default=uuid.uuid4, blank=True, editable=False)
    # Add more user profile fields here. Make sure they are nullable
    # or with default values
    picture = models.ImageField(_('Profile picture'),
                                upload_to='profile_pics/%Y-%m-%d/',
                                null=True,
                                blank=True)
    bio = models.CharField(_("Short Bio"), max_length=200, blank=True, null=True)
    email_verified = models.BooleanField(_("Email verified"), default=False)
    tracking = models.BooleanField(_("Location tracking"), default=False)
    Latitude = models.FloatField(_("Last known latitude"),null=True,blank=True)
    Longitude = models.FloatField(_("Last known longitude"),null=True,blank=True)
    Accuracy = models.FloatField(_("Last known position accuracy"),null=True,blank=True)
    LastUpdated= models.DateTimeField(help_text='Datetime of the last data',blank = True,null=True)
    
    class Meta:
        abstract = True
        permissions = (
            ("view_tracking", "Can see the real time ubication of a user"),
            ("change_trackingstate", "Can change the state of the tracking of a user"),
        )

@receiver(post_save)
def update_BaseProfile(sender, instance, update_fields,**kwargs):
    if issubclass(sender, BaseProfile):
        from Tracks.models import BeaconModel
        beacons=BeaconModel.objects.all()
        from HomeAutomation.models import MainDeviceVarModel
        for beacon in beacons:
            label='Distance from ' + instance.user.name + ' to ' + str(beacon) 
            timestamp=timezone.now()
            try:
                mainVar=MainDeviceVarModel.objects.get(Label=label)
            except:
                mainVar=MainDeviceVarModel(Label=label,Value='',Datatype=0,Units='km',UserEditable=False)
                logger.info('Creating main Var ' + label)

            if instance.Latitude!=None and instance.Longitude!=None:
                newValue=beacon.distance_to(other=instance)
            else:
                newValue=-1
            mainVar.update_value(newValue=newValue,timestamp=timestamp,writeDB=True)
            PublishEvent(Severity=0,Text=label+' is ' + str(mainVar.Value),Persistent=False)
        if instance.Latitude!=None and instance.Longitude!=None:
            import json
            from tzlocal import get_localzone
            local_tz=get_localzone()
            localdate = local_tz.localize(instance.LastUpdated.replace(tzinfo=None))
            localdate=localdate+localdate.utcoffset() 
            Group('Profiles-values').send({'text':json.dumps({'user': instance.user.name,'Latitude':instance.Latitude,'Longitude':instance.Longitude,'Accuracy':instance.Accuracy,
                                            'LastUpdated':localdate.strftime("%d %B %Y %H:%M:%S")})},immediately=True)

@python_2_unicode_compatible
class Profile(BaseProfile):
    def __str__(self):
        return "{}'s profile". format(self.user)
