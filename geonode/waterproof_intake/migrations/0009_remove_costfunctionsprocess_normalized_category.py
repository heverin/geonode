# Generated by Django 2.2.16 on 2021-01-08 20:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('waterproof_intake', '0008_auto_20210108_2028'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='costfunctionsprocess',
            name='normalized_category',
        ),
    ]
