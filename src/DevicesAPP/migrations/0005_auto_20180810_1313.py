# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-08-10 11:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('DevicesAPP', '0004_auto_20180430_1112'),
    ]

    operations = [
        migrations.CreateModel(
            name='CronExpressions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Identifier', models.CharField(max_length=50, unique=True)),
                ('DayOfWeek', models.CharField(blank=True, default='?', help_text='Days in the week that it will trigger.  "1-3" will trigger it on Mon., Tue. and Wed. of the week, "1,3" will trigger it only on Mon. and Wed., "*/2" will trigger every two days, leaving it blank or setting an "*" will trigger it every day.', max_length=20)),
                ('Month', models.CharField(blank=True, default='*', help_text='Months that it will trigger.  "1-3" will trigger it on Jan., Febr. and March, "1,3" will trigger it only on Jan. and March, "*/2" will trigger every two months, leaving it blank or setting an "*" will trigger it every month.', max_length=20)),
                ('DayOfMonth', models.CharField(blank=True, default='*', help_text='Days that it will trigger.  "1-3" will trigger it on the 1st, 2nd and 3rd day of the month, "1,3" will trigger it only on 1st and 3rd, "*/2" will trigger every two days, leaving it blank or setting an "*" will trigger it every day.', max_length=20)),
                ('Hours', models.CharField(blank=True, default='0', help_text='Hours that it will trigger.  "1-3" will trigger it at 1, 2 and 3 a.m., "1,3" will trigger it only at 1 and 3 p.m., "*/2" will trigger every two hours, leaving it blank or setting an "*" will trigger it every hour.', max_length=20)),
                ('Minutes', models.CharField(blank=True, default='0', help_text='Minutes that it will trigger.  "1-3" will trigger it at minutes 1, 2 and 3, "1,3" will trigger it only at minutes 1 and 3 , "*/2" will trigger every two minutes, leaving it blank or setting an "*" will trigger it every minute.', max_length=20)),
                ('Seconds', models.CharField(blank=True, default='0', help_text='Seconds that it will trigger.  "1-3" will trigger it at seconds 1, 2 and 3, "1,3" will trigger it only at seconds 1 and 3 , "*/2" will trigger every two seconds, Setting an "*" will trigger it every second.', max_length=20)),
            ],
            options={
                'verbose_name': 'Cron expression',
                'verbose_name_plural': 'Cron expressions',
            },
        ),
        migrations.AlterField(
            model_name='datagrams',
            name='Type',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Synchronous'), (1, 'Asynchronous'), (2, 'Cronned')]),
        ),
        migrations.AddField(
            model_name='datagrams',
            name='Cron',
            field=models.ForeignKey(blank=True, help_text='The cron expression that controls the polling. Only applies to cronned datagrams.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='datagrams', to='DevicesAPP.CronExpressions'),
        ),
    ]
