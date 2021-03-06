# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-18 12:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('DevicesAPP', '0008_auto_20180917_1415'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cronexpressions',
            name='DayOfWeek',
            field=models.CharField(blank=True, default='*', help_text='Days in the week that it would trigger.  "1-3" would trigger it on Mon., Tue. and Wed. of the week, "1,3" would trigger it only on Mon. and Wed., "*/2" would trigger every two days, leaving it blank or setting an "*" would trigger it every day.', max_length=20),
        ),
    ]
