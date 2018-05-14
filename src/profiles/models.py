# coding: utf-8
from __future__ import unicode_literals
from django.utils.translation import ugettext as _
import uuid
from channels.binding.websockets import WebsocketBinding
import sys

from django.utils import timezone
from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.dispatch import receiver
from django.db.models.signals import post_save,post_delete,pre_delete
from channels import Group
from EventsAPP.consumers import PublishEvent

import logging

logger = logging.getLogger("project")

SQL_createTracks_table = ''' 
                                CREATE TABLE IF NOT EXISTS tracks (
                                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    User text NOT NULL,
                                    Latitude float NOT NULL,
                                    Longitude float NOT NULL,
                                    Accuracy float NOT NULL,
                                    UNIQUE (timestamp,User)                    
                                ); 
                                '''
SQLinsertTrack_statement = ''' INSERT INTO tracks (timestamp,User,Latitude,Longitude,Accuracy) VALUES(?,?,?,?,?) ''' # the ? will be replaced by the values


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
    
    def updateLocationData(self,Latitude,Longitude,Accuracy):
        if self.tracking:
            timestamp=timezone.now()
            self.Latitude=Latitude
            self.Longitude=Longitude
            self.Accuracy=Accuracy
            self.LastUpdated=timestamp
            self.save()
            timestamp=timezone.now()
            self.insertTrackRegister(TimeStamp=timestamp,Latitude=Latitude,Longitude=Longitude,Accuracy=Accuracy)
    
    
    @staticmethod
    def createRegistersDBTable():
        import utils.BBDD
        DBinstance=utils.BBDD.getRegistersDBInstance()
        if not DBinstance.checkIfTableExist(table='tracks'):
            try:
                sql=SQL_createTracks_table
                DBinstance.executeTransactionWithCommit(SQLstatement=sql)                              
            except:
                PublishEvent(Severity=3,Text="Unexpected error in create_tracks_table: "+ sys.exc_info()[1],Persistent=True,Code='Profiles-10')
    
    def insertTrackRegister(self,TimeStamp,Latitude,Longitude,Accuracy):
        import utils.BBDD
        self.createRegistersDBTable()
        DBinstance=utils.BBDD.getRegistersDBInstance()
        sql=SQLinsertTrack_statement
        try:
            DBinstance.executeTransactionWithCommit(SQLstatement=sql,arg=[TimeStamp,str(self.user.email),Latitude,Longitude,Accuracy])
        except:
            PublishEvent(Severity=3,Text="Unexpected error in insert_track: "+ sys.exc_info()[1],Persistent=True,Code='Profiles-10')
            
    class Meta:
        abstract = True
        permissions = (
            ("view_tracking", "Can see the real time ubication of a user"),
            ("change_trackingstate", "Can change the state of the tracking of a user"),
        )

@receiver(post_save)
def update_BaseProfile(sender, instance, update_fields,**kwargs):
    
    if issubclass(sender, BaseProfile) and instance.tracking:
        from DevicesAPP.models import Beacons
        from DevicesAPP.constants import DTYPE_FLOAT
        import MainAPP.models
        import MainAPP.signals
        beacons=Beacons.objects.all()
        #print('Found ' + str(beacons.count()) + ' beacons')
        for beacon in beacons:
            label='Distance from ' + instance.user.name + ' to ' + str(beacon) 
            timestamp=timezone.now()
            data={'Label':label,'Value':-1,'DataType':DTYPE_FLOAT,'Units':'km','UserEditable':False}
            MainAPP.signals.SignalCreateMainDeviceVars.send(sender=None,Data=data)
            #print('Send signal to create MainVar ' + str(data))
            if instance.Latitude!=None and instance.Longitude!=None:
                newValue=beacon.distance_to(other=instance)
            else:
                newValue=-1
            
            #print('MainVar value ' + str(newValue))
            avar=MainAPP.models.AutomationVariables.objects.get(Device='MainVars',Label=data['Label'])
            MainAPP.signals.SignalUpdateValueMainDeviceVars.send(sender=None,Tag=avar.Tag,timestamp=timestamp,newValue=newValue)
            PublishEvent(Severity=0,Text=label+' is ' + str(avar.getLatestValue),Persistent=False,Code='Profiles-0')
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
