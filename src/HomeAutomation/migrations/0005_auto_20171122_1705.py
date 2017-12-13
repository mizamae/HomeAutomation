# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-11-22 16:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HomeAutomation', '0004_maindevicevarmodel_plottype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='maindevicevarmodel',
            name='PlotType',
            field=models.CharField(choices=[('line', 'Hard Line'), ('spline', 'Smoothed Line'), ('column', 'Bars')], default='line', max_length=10),
        ),
    ]