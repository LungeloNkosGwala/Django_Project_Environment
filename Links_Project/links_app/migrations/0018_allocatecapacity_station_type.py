# Generated by Django 3.2.5 on 2023-01-05 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('links_app', '0017_allocatecapacity'),
    ]

    operations = [
        migrations.AddField(
            model_name='allocatecapacity',
            name='station_type',
            field=models.CharField(default='', max_length=30),
            preserve_default=False,
        ),
    ]
