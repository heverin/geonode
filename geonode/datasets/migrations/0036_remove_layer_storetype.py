# Generated by Django 3.2.4 on 2021-07-06 13:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0035_auto_20210525_0847'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='Dataset',
            name='storeType',
        ),
    ]
