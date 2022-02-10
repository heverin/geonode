# Generated by Django 3.2.12 on 2022-02-10 14:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0077_merge_20220204_1347'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcebase',
            name='metadata',
            field=models.ManyToManyField(blank=True, help_text='Additional metadata, must be in format [ {"metadata_key": "metadata_value"}, {"metadata_key": "metadata_value"} ]', null=True, to='base.ExtraMetadata', verbose_name='Extra Metadata'),
        ),
    ]
