# Generated by Django 3.2.15 on 2022-09-29 15:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("upload", "0040_importer_introduction"),
    ]

    operations = [
        migrations.AddField(
            model_name="resourcehandlerinfo",
            name="kwargs",
            field=models.JSONField(
                default=dict,
                verbose_name="Storing strictly related information of the handler",
            ),
        ),
    ]
