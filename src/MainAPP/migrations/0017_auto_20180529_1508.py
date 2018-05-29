# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-29 13:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MainAPP', '0016_auto_20180529_1324'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='AUTODENY_ATTEMPTS',
            field=models.PositiveSmallIntegerField(default=40, help_text='The number of denied accesses in 24h that will result in an IP blocked.', verbose_name='Number of denied attempts to block an IP'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='PROXY_AUTO_DENYIP',
            field=models.BooleanField(default=True, help_text='Feature that blocks automatically WAN IPs with more than in 24 h.', verbose_name='Enable automatic IP blocking'),
        ),
    ]
