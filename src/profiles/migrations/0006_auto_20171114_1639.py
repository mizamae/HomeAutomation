# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-11-14 15:39
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0005_profile_accuracy'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profile',
            options={'permissions': (('view_tracking', 'Can see the real time ubication of a user'), ('change_trackingstate', 'Can change the state of the tracking of a user'))},
        ),
    ]