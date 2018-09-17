# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-17 12:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('DevicesAPP', '0007_auto_20180905_0848'),
    ]

    operations = [
        migrations.AddField(
            model_name='mastergpios',
            name='LabelFalse',
            field=models.CharField(blank=True, default='', help_text='Label for the notification when the IO is False.', max_length=150),
        ),
        migrations.AddField(
            model_name='mastergpios',
            name='LabelTrue',
            field=models.CharField(blank=True, default='', help_text='Label for the notification when the IO is True.', max_length=150),
        ),
    ]
