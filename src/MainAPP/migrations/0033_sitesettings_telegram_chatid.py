# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-12-26 08:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MainAPP', '0032_auto_20181217_1419'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='TELEGRAM_CHATID',
            field=models.CharField(blank=True, default='', help_text='The ID of the chat to use', max_length=100, verbose_name='Chat ID'),
        ),
    ]
