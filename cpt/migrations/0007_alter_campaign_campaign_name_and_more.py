# Generated by Django 4.2.9 on 2024-08-08 15:55

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cpt", "0006_campaign_form_enabled_alter_campaign_allow_drawings_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="campaign",
            name="campaign_name",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="campaign",
            name="campaing_detailed_description",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="campaign",
            name="campaing_short_description",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="campaign",
            name="campaing_title",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="campaign",
            name="start_date",
            field=models.DateTimeField(
                default=datetime.datetime(2024, 8, 8, 15, 55, 12, 621375, tzinfo=datetime.timezone.utc)
            ),
        ),
    ]
