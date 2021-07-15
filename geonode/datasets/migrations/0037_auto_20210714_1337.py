# Generated by Django 3.2.4 on 2021-07-14 13:37

from django.db import migrations, models
import django.db.migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0036_remove_layer_storetype'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dataset',
            options={'permissions': (('change_dataset_data', 'Can edit layer data'), ('change_dataset_style', 'Can change layer style'))},
        ),
        migrations.AlterField(
            model_name='dataset',
            name='default_style',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dataset_default_style', to='datasets.style'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='styles',
            field=models.ManyToManyField(related_name='dataset_styles', to='datasets.Style'),
        )
    ]
