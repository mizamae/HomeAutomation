# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-11-07 14:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HomeAutomation', '0008_auto_20171107_1252'),
    ]

    operations = [
        migrations.AddField(
            model_name='automationrulemodel',
            name='Var2Hyst',
            field=models.DecimalField(decimal_places=2, default=0.5, max_digits=6),
        ),
    ]