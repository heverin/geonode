# Generated by Django 3.2.18 on 2023-03-30 07:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0089_alter_resourcebase_use_constrains'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resourcebase',
            name='restriction_code_type',
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='restriction_code_type',
            field=models.ManyToManyField(blank=True, help_text='limitation(s) placed upon the access or use of the data.', limit_choices_to=models.Q(('is_choice', True)), null=True, related_name='restriction_code_type', to='base.RestrictionCodeType', verbose_name='restrictions'),
        ),
        migrations.RemoveField(
            model_name='resourcebase',
            name='use_constrains',
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='use_constrains',
            field=models.ManyToManyField(blank=True, help_text='This metadata element shall provide information on the Use constraints applied to assure the protection of privacy or intellectual property (e.g. Trademark)', limit_choices_to=models.Q(('is_choice', True)), null=True, related_name='use_constrains', to='base.RestrictionCodeType', verbose_name='use_constrains'),
        ),
    ]
