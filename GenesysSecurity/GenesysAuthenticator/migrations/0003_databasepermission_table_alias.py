# Generated by Django 4.2 on 2024-01-29 10:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GenesysAuthenticator', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='databasepermission',
            name='table_alias',
            field=models.CharField(choices=[('admin_al', 'admin_al'), ('road_al', 'road_al')], default=1, max_length=255),
            preserve_default=False,
        ),
    ]
