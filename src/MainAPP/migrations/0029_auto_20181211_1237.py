# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-12-11 11:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MainAPP', '0028_auto_20181122_1802'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='ESIOS_TOKEN',
            field=models.CharField(default='', help_text='The token assigned by the ESIOS service. You should ask for yours to: Consultas Sios <consultasios@ree.es>', max_length=50, verbose_name='Token for the ESIOS page'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='IBERDROLA_PASSW',
            field=models.CharField(default='', help_text='Password registered on the Iberdrola Distribucion webpage', max_length=50, verbose_name='Iberdrola password'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='IBERDROLA_USER',
            field=models.CharField(default='', help_text='Username registered into the Iberdrola Distribucion webpage', max_length=50, verbose_name='Iberdrola username'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='OWM_TOKEN',
            field=models.CharField(default='', help_text='The token assigned by the OpenWeatherMap service. You should ask yours following https://openweathermap.org/appid', max_length=50, verbose_name='Token for the openweathermap page'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='TELEGRAM_TOKEN',
            field=models.CharField(default='', help_text='The token assigned by the BothFather', max_length=50, verbose_name='Token for the telegram bot'),
        ),
    ]
