# Generated by Django 2.2.16 on 2021-01-05 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0037_auto_20201222_1250'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='professional_role',
            field=models.CharField(blank=True, choices=[('ADMIN', 'Administrator'), ('ANALYST', 'Analyst'), ('COPART', 'Corporate partner'), ('ACDMC', 'Academic'), ('SCADM', 'Service company administrator'), ('MCOMC', 'Manager that carries out monitoring and control'), ('CITIZN', 'Citizen'), ('REPECS', 'Representative of an economic sector'), ('OTHER', 'Other')], help_text='Professional or Academic user role', max_length=6, null=True, verbose_name='ProfessionalRole'),
        ),
    ]
