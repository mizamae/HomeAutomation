# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-14 10:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0004_auto_20171114_1100'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='Latitude',
            field=models.FloatField(default=0, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='Longitude',
            field=models.FloatField(default=0, null=True),
        ),
    ]
