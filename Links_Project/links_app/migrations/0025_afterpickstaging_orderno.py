# Generated by Django 3.2.5 on 2023-01-25 17:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('links_app', '0024_auto_20230114_2225'),
    ]

    operations = [
        migrations.AddField(
            model_name='afterpickstaging',
            name='orderno',
            field=models.CharField(default='', max_length=30),
            preserve_default=False,
        ),
    ]
