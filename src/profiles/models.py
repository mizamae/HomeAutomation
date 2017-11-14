# coding: utf-8
from __future__ import unicode_literals
from django.utils.translation import ugettext as _
import uuid

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.dispatch import receiver
from django.db.models.signals import post_save,post_delete,pre_delete

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
    
    class Meta:
        abstract = True

@receiver(post_save)
def update_BaseProfile(sender, instance, update_fields,**kwargs):
    if issubclass(sender, BaseProfile):
        from Tracks.models import BeaconModel
        beacons=BeaconModel.objects.all()
        from HomeAutomation.models import MainDeviceVarModel
        for beacon in beacons:
            label=_('Distance from ') + instance.user.name + _(' to ') + str(beacon) 
            try:
                mainVar=MainDeviceVarModel.objects.get(Label=label)
            except:
                mainVar=MainDeviceVarModel(Label=label,Value='',Datatype=0,Units='km')

            if instance.Latitude!=None and instance.Longitude!=None:
                mainVar.Value=beacon.distance_to(other=instance)
            else:
                mainVar.Value=-1
            mainVar.save()

@python_2_unicode_compatible
class Profile(BaseProfile):
    def __str__(self):
        return "{}'s profile". format(self.user)
