# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-15 12:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MainAPP', '0025_auto_20181003_2118'),
    ]

    operations = [
        migrations.AddField(
            model_name='additionalcalculations',
            name='Timespan',
            field=models.PositiveSmallIntegerField(choices=[(0, 'An hour'), (1, 'A day'), (2, 'A week'), (3, 'A month')], default=1, help_text='What is the time span for the calculation'),
        ),
    ]
