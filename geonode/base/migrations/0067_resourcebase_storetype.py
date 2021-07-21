# Generated by Django 3.2.4 on 2021-07-06 08:48

from django.db import migrations, models
from django.db.migrations import RunSQL, RunPython

LAYERS_SUBTYPES = {
    "dataStore": "vector",
    "coverageStore": "raster",
    "remoteStore": "remote",
    "vectorTimeSeries": "vector_time"
}

clone_layers_storetypes = '''
UPDATE base_resourcebase
SET "storetype"=subquery."storeType"
FROM (select resourcebase_ptr_id,"storeType" from layers_layer gg) AS subquery
WHERE base_resourcebase.id=subquery.resourcebase_ptr_id;
'''

clone_documents_storetypes = '''
UPDATE base_resourcebase
SET "storetype"=subquery."doc_type"
FROM (select resourcebase_ptr_id,"doc_type" from documents_document gg) AS subquery
WHERE base_resourcebase.id=subquery.resourcebase_ptr_id;
'''


def update_storetype_value(apps, schema_editor):
    MyModel = apps.get_model('layers', 'Layer')
    for l in MyModel.objects.filter(storetype__in=(LAYERS_SUBTYPES.keys())):
        u = MyModel.objects.filter(resourcebase_ptr_id=l.resourcebase_ptr_id)
        store_type = (lambda element: LAYERS_SUBTYPES.get(element, element))(l.storetype)
        u.update(storetype=store_type)


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0032_remove_document_doc_file'),
        ('layers', '0035_auto_20210525_0847'),
        ('base', '0066_resourcebase_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcebase',
            name='storetype',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        RunSQL(clone_layers_storetypes),
        RunSQL(clone_documents_storetypes),
        RunPython(update_storetype_value)
    ]
