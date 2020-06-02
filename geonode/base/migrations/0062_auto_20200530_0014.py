# Generated by Django 2.2.11 on 2020-05-30 00:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0061_auto_20200530_0008'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmbrapaUnity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unity', models.CharField(max_length=20)),
            ],
            options={
                'verbose_name_plural': 'Unidades',
                'ordering': ('unity',),
            },
        ),
        migrations.CreateModel(
            name='PurposeEmbrapa',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(max_length=300)),
                ('project_code', models.IntegerField(default=0)),
                ('title', models.TextField(default='')),
            ],
            options={
                'verbose_name_plural': 'Finalidades',
                'ordering': ('title',),
            },
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='purpose_embrapa',
            field=models.ForeignKey(blank=True, help_text='Escolha a finalidade do metadado', null=True, on_delete=django.db.models.deletion.CASCADE, to='base.PurposeEmbrapa', verbose_name='PurposeEmbrapa'),
        ),
    ]
