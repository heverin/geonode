# Generated by Django 2.2.16 on 2020-12-17 03:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('waterproof_nbs_ca', '0021_auto_20201217_0320'),
    ]

    operations = [
        migrations.AlterField(
            model_name='waterproofnbsca',
            name='unit_implementation_cost',
            field=models.FloatField(default=0, verbose_name='Unit implementation costs (US $/ha)'),
        ),
    ]
