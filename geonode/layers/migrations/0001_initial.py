# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('base', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0001_initial'),
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attribute', models.CharField(help_text='name of attribute as stored in shapefile/spatial database', max_length=255, null=True, verbose_name='attribute name')),
                ('description', models.CharField(help_text='description of attribute to be used in metadata', max_length=255, null=True, verbose_name='attribute description', blank=True)),
                ('attribute_label', models.CharField(help_text='title of attribute as displayed in GeoNode', max_length=255, null=True, verbose_name='attribute label', blank=True)),
                ('attribute_type', models.CharField(default=b'xsd:string', help_text='the data type of the attribute (integer, string, geometry, etc)', max_length=50, verbose_name='attribute type')),
                ('visible', models.BooleanField(default=True, help_text='specifies if the attribute should be displayed in identify results', verbose_name='visible?')),
                ('display_order', models.IntegerField(default=1, help_text='specifies the order in which attribute should be displayed in identify results', verbose_name='display order')),
                ('count', models.IntegerField(default=1, help_text='count value for this field', verbose_name='count')),
                ('min', models.CharField(default=b'NA', max_length=255, null=True, verbose_name='min', help_text='minimum value for this field')),
                ('max', models.CharField(default=b'NA', max_length=255, null=True, verbose_name='max', help_text='maximum value for this field')),
                ('average', models.CharField(default=b'NA', max_length=255, null=True, verbose_name='average', help_text='average value for this field')),
                ('median', models.CharField(default=b'NA', max_length=255, null=True, verbose_name='median', help_text='median value for this field')),
                ('stddev', models.CharField(default=b'NA', max_length=255, null=True, verbose_name='standard deviation', help_text='standard deviation for this field')),
                ('sum', models.CharField(default=b'NA', max_length=255, null=True, verbose_name='sum', help_text='sum value for this field')),
                ('unique_values', models.TextField(default=b'NA', null=True, verbose_name='unique values for this field', blank=True)),
                ('last_stats_updated', models.DateTimeField(default=datetime.datetime.now, help_text='date when attribute statistics were last updated', verbose_name='last modified')),
            ],
        ),
        migrations.CreateModel(
            name='Layer',
            fields=[
                ('resourcebase_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='base.ResourceBase')),
                ('title_en', models.CharField(help_text='name by which the cited resource is known', max_length=255, null=True, verbose_name='title')),
                ('abstract_en', models.TextField(help_text='brief narrative summary of the content of the resource(s)', null=True, verbose_name='abstract', blank=True)),
                ('purpose_en', models.TextField(help_text='summary of the intentions with which the resource(s) was developed', null=True, verbose_name='purpose', blank=True)),
                ('constraints_other_en', models.TextField(help_text='other restrictions and legal prerequisites for accessing and using the resource or metadata', null=True, verbose_name='restrictions other', blank=True)),
                ('supplemental_information_en', models.TextField(default='No information provided', help_text='any other descriptive information about the dataset', null=True, verbose_name='supplemental information')),
                ('data_quality_statement_en', models.TextField(help_text="general explanation of the data producer's knowledge about the lineage of a dataset", null=True, verbose_name='data quality statement', blank=True)),
                ('workspace', models.CharField(max_length=128)),
                ('store', models.CharField(max_length=128)),
                ('storeType', models.CharField(max_length=128)),
                ('name', models.CharField(max_length=128)),
                ('typename', models.CharField(max_length=128, null=True, blank=True)),
                ('is_mosaic', models.BooleanField(default=False)),
                ('has_time', models.BooleanField(default=False)),
                ('has_elevation', models.BooleanField(default=False)),
                ('time_regex', models.CharField(blank=True, max_length=128, null=True, choices=[(b'[0-9]{8}', 'YYYYMMDD'), (b'[0-9]{8}T[0-9]{6}', "YYYYMMDD'T'hhmmss"), (b'[0-9]{8}T[0-9]{6}Z', "YYYYMMDD'T'hhmmss'Z'")])),
                ('elevation_regex', models.CharField(max_length=128, null=True, blank=True)),
                ('charset', models.CharField(default=b'UTF-8', max_length=255)),
                
            ],
            options={
                'permissions': (('change_layer_data', 'Can edit layer data'), ('change_layer_style', 'Can change layer style')),
            },
            bases=('base.resourcebase',),
        ),
        migrations.CreateModel(
            name='LayerAuditActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('result', models.CharField(max_length=15, choices=[(b'APPROVED', 'Approved'), (b'DECLEINED', 'Decleined'), (b'CANCELED', 'Canceled')])),
                ('comment_subject', models.CharField(help_text='Comment type to approve or deny layer submission ', max_length=300)),
                ('comment_body', models.TextField(help_text='Comments when auditor denied or approved layer submission', blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('auditor', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='LayerFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('base', models.BooleanField(default=False)),
                ('file', models.FileField(max_length=255, upload_to=b'layers')),
            ],
        ),
        migrations.CreateModel(
            name='LayerStyles',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('layer', models.ForeignKey(to='layers.Layer')),
            ],
        ),
        migrations.CreateModel(
            name='LayerSubmissionActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('iteration', models.IntegerField(default=0)),
                ('is_audited', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('group', models.ForeignKey(to='groups.GroupProfile')),
                ('layer', models.ForeignKey(related_name='layer_submission', to='layers.Layer')),
            ],
        ),
        migrations.CreateModel(
            name='Style',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='style name')),
                ('sld_title', models.CharField(max_length=255, null=True, blank=True)),
                ('sld_body', models.TextField(null=True, verbose_name='sld text', blank=True)),
                ('sld_version', models.CharField(max_length=12, null=True, verbose_name='sld version', blank=True)),
                ('sld_url', models.CharField(max_length=1000, null=True, verbose_name='sld url')),
                ('workspace', models.CharField(max_length=255, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='UploadSession',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now=True)),
                ('processed', models.BooleanField(default=False)),
                ('error', models.TextField(null=True, blank=True)),
                ('traceback', models.TextField(null=True, blank=True)),
                ('context', models.TextField(null=True, blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='layerstyles',
            name='style',
            field=models.ForeignKey(to='layers.Style'),
        ),
        migrations.AddField(
            model_name='layerfile',
            name='upload_session',
            field=models.ForeignKey(to='layers.UploadSession'),
        ),
        migrations.AddField(
            model_name='layerauditactivity',
            name='layer_submission_activity',
            field=models.ForeignKey(to='layers.LayerSubmissionActivity'),
        ),
        migrations.AddField(
            model_name='layer',
            name='default_style',
            field=models.ForeignKey(related_name='layer_default_style', blank=True, to='layers.Style', null=True),
        ),
        migrations.AddField(
            model_name='layer',
            name='service',
            field=models.ForeignKey(related_name='layer_set', blank=True, to='services.Service', null=True),
        ),
        migrations.AddField(
            model_name='layer',
            name='styles',
            field=models.ManyToManyField(related_name='LayerStyles', to='layers.Style'),
        ),
        migrations.AddField(
            model_name='layer',
            name='upload_session',
            field=models.ForeignKey(blank=True, to='layers.UploadSession', null=True),
        ),
        migrations.AddField(
            model_name='attribute',
            name='layer',
            field=models.ForeignKey(related_name='attribute_set', to='layers.Layer'),
        ),
        migrations.AlterUniqueTogether(
            name='layersubmissionactivity',
            unique_together=set([('layer', 'group', 'iteration')]),
        ),
    ]
