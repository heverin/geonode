# Generated by Django 3.2.7 on 2021-11-19 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0073_resourcebase_thumbnail_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcebase',
            name='was_approved',
            field=models.BooleanField(default=True, help_text='Previous Approved state.', verbose_name='Was Approved'),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='was_published',
            field=models.BooleanField(default=True, help_text='Previous Published state.', verbose_name='Was Published'),
        ),
    ]
