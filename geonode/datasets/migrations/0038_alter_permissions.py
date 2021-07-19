# Generated by Django 3.2.4 on 2021-07-14 13:37

from django.db import migrations, models
from django.db import connection, migrations
from django.db.models import deletion


def alter_permissions(apps, schema_editor):
    try:
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        layer_ctype = ContentType.objects.filter(app_label='layers', model='layer')
        dataset_ctype, _ = ContentType.objects.get_or_create(app_label='datasets', model='dataset')
        if layer_ctype.exists():
            perms = Permission.objects.filter(content_type=layer_ctype.first())
            for perm in perms:
                perm.codename = perm.codename.replace('layer', 'dataset')
                perm.content_type=dataset_ctype
                perm.save()

    except Exception as e:
        raise e

class Migration(migrations.Migration):
    atomic= True
    dependencies = [
        ('harvesting', '0026_harvestableresource_last_harvesting_succeeded'),
        ('upload', '0033_auto_20210531_1252'),
        ('base', '0068_rename_storetype_resourcebase_subtype'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('services', '0045_auto_20210629_1355'),
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
            field=models.ForeignKey(blank=True, null=True, on_delete=deletion.SET_NULL, related_name='dataset_default_style', to='datasets.style'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='styles',
            field=models.ManyToManyField(related_name='dataset_styles', to='datasets.Style'),
        ),
        migrations.RunPython(alter_permissions),
    ]
