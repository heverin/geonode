# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-04 08:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [(b'geonode_client', '0002_auto_20180412_1039'), (b'geonode_client', '0003_geonodethemecustomization_jumbotron_welcome_hide'), (b'geonode_client', '0004_auto_20180416_1319'), (b'geonode_client', '0005_auto_20181015_1201')]

    dependencies = [
        ('geonode_client', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='partners_title',
            field=models.CharField(blank=True, default=b'Our Partners', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='jumbotron_welcome_hide',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='jumbotron_site_description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='jumbotron_welcome_content',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='geonodethemecustomization',
            name='jumbotron_welcome_title',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.DeleteModel(
            name='GeoNodeThemeCustomization',
        ),
    ]
