# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-18 09:41
from __future__ import unicode_literals

import Devices.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Master_GPIOs', '0002_auto_20171011_1529'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommandModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Identifier', models.CharField(max_length=10)),
                ('HumanTag', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'Command',
                'verbose_name_plural': 'Commands',
            },
        ),
        migrations.CreateModel(
            name='DatagramModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Identifier', models.CharField(max_length=20)),
                ('Code', models.PositiveSmallIntegerField(help_text='Identifier byte-type code')),
                ('Type', models.CharField(choices=[('Synchronous', 'Synchronous'), ('Asynchronous', 'Asynchronous')], max_length=12)),
            ],
            options={
                'verbose_name': 'Datagram',
                'verbose_name_plural': 'Datagrams',
            },
        ),
        migrations.CreateModel(
            name='DeviceModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('DeviceName', models.CharField(error_messages={'unique': 'Invalid device name - This name already exists in the DB.'}, max_length=50, unique=True)),
                ('DeviceCode', models.IntegerField(blank=True, error_messages={'unique': 'Invalid device code - This code already exists in the DB.'}, null=True, unique=True)),
                ('DeviceIP', models.GenericIPAddressField(blank=True, error_messages={'unique': 'Invalid IP - This IP already exists in the DB.'}, null=True, protocol='IPv4', unique=True)),
                ('DeviceState', models.CharField(choices=[('STOPPED', 'STOPPED'), ('RUNNING', 'RUNNING')], default='STOPPED', max_length=15)),
                ('Sampletime', models.PositiveIntegerField(default=600)),
                ('RTsampletime', models.PositiveIntegerField(default=60)),
                ('LastUpdated', models.DateTimeField(blank=True, null=True)),
                ('Connected', models.BooleanField(default=False)),
                ('CustomLabels', models.CharField(blank=True, default='', max_length=1500)),
                ('Error', models.CharField(blank=True, default='', max_length=100)),
                ('IO', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pin2device', to='Master_GPIOs.IOmodel')),
            ],
            options={
                'verbose_name': 'Slave device',
                'verbose_name_plural': 'Slave devices',
                'permissions': (('view_devices', 'Can see available devices'), ('change_state', 'Can change the state of the devices'), ('add_device', 'Can add new devices to the installation')),
            },
        ),
        migrations.CreateModel(
            name='DeviceTypeModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Code', models.CharField(max_length=20, unique=True)),
                ('Description', models.CharField(max_length=50)),
                ('MinSampletime', models.PositiveIntegerField(default=10)),
                ('Connection', models.CharField(choices=[('LOCAL', 'LOCAL'), ('REMOTE', 'REMOTE'), ('MEMORY', 'MEMORY')], max_length=15)),
                ('Picture', models.ImageField(blank=True, null=True, upload_to=Devices.models.path_file_name, verbose_name='DeviceType picture')),
            ],
            options={
                'verbose_name': 'Device type',
                'verbose_name_plural': 'Device types',
            },
        ),
        migrations.CreateModel(
            name='ItemModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('HumanTag', models.CharField(max_length=20, unique=True)),
                ('DataType', models.CharField(choices=[('INTEGER', 'Analog Integer'), ('FLOAT', 'Analog Float'), ('DIGITAL', 'Digital')], max_length=10)),
                ('Units', models.CharField(max_length=10, null=True)),
            ],
            options={
                'verbose_name': 'Datagram item',
                'verbose_name_plural': 'Datagram items',
            },
        ),
        migrations.CreateModel(
            name='ItemOrdering',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveSmallIntegerField(help_text='Position in the dataframe 1-based')),
                ('Item', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Devices.ItemModel')),
                ('datagram', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Devices.DatagramModel')),
            ],
            options={
                'verbose_name': 'Item',
                'verbose_name_plural': 'Items',
                'ordering': ('order',),
            },
        ),
        migrations.CreateModel(
            name='ReportItems',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fromDate', models.DateTimeField(blank=True, editable=False, null=True)),
                ('toDate', models.DateTimeField(blank=True, editable=False, null=True)),
                ('data', models.CharField(blank=True, help_text='Data of the report in JSON format', max_length=20000, null=True)),
            ],
            options={
                'verbose_name': 'Generated report',
                'verbose_name_plural': 'Generated reports',
                'ordering': ('fromDate',),
            },
        ),
        migrations.CreateModel(
            name='ReportModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ReportTitle', models.CharField(error_messages={'unique': 'Invalid report title - This title already exists in the DB.'}, max_length=50, unique=True)),
                ('Periodicity', models.PositiveSmallIntegerField(choices=[(2, 'Every day'), (3, 'Every week'), (4, 'Every month')], help_text='How often the report will be generated')),
                ('DataAggregation', models.PositiveSmallIntegerField(choices=[(0, 'No aggregation'), (1, 'Hourly'), (2, 'Daily'), (4, 'Monthly')], help_text='Data directly from the DB or averaged over a period')),
                ('ReportContentJSON', models.CharField(help_text='Content of the report in JSON format', max_length=20000)),
            ],
            options={
                'verbose_name': 'Report',
                'verbose_name_plural': 'Reports',
                'permissions': (('add_report', 'Can configure and add reports'), ('view_report', 'Can view reports configured'), ('view_plots', 'Can see the historic plots from any device')),
            },
        ),
        migrations.AddField(
            model_name='reportitems',
            name='Report',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Devices.ReportModel'),
        ),
        migrations.AddField(
            model_name='devicemodel',
            name='Type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deviceType', to='Devices.DeviceTypeModel'),
        ),
        migrations.AddField(
            model_name='datagrammodel',
            name='DeviceType',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Devices.DeviceTypeModel'),
        ),
        migrations.AddField(
            model_name='datagrammodel',
            name='Items',
            field=models.ManyToManyField(through='Devices.ItemOrdering', to='Devices.ItemModel'),
        ),
        migrations.AddField(
            model_name='commandmodel',
            name='DeviceType',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Devices.DeviceTypeModel'),
        ),
        migrations.AlterUniqueTogether(
            name='reportitems',
            unique_together=set([('Report', 'fromDate', 'toDate')]),
        ),
        migrations.AlterUniqueTogether(
            name='datagrammodel',
            unique_together=set([('DeviceType', 'Identifier'), ('DeviceType', 'Code')]),
        ),
        migrations.AlterUniqueTogether(
            name='commandmodel',
            unique_together=set([('DeviceType', 'Identifier')]),
        ),
    ]
