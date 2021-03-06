# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-12-17 13:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MainAPP', '0030_auto_20181211_1246'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitesettings',
            name='ESIOS_TOKEN',
            field=models.CharField(blank=True, default='', help_text='The token assigned by the ESIOS service. You should ask for yours to: Consultas Sios <consultasios@ree.es>', max_length=100, verbose_name='Token for the ESIOS page'),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='TELEGRAM_TOKEN',
            field=models.CharField(blank=True, default='', help_text='The token assigned by the BothFather', max_length=100, verbose_name='Token for the telegram bot'),
        ),
    ]
