# Generated by Django 3.2.23 on 2024-08-22 09:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0045_alter_dataset_abstract_en'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='constraints_other_en',
            field=models.TextField(blank=True, help_text='other restrictions and legal prerequisites for accessing and using the resource or metadata by User', null=True, verbose_name='restrictions other'),
        ),
    ]
