# Generated by Django 3.2.5 on 2023-01-14 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('links_app', '0019_bincontent_avail_qty'),
    ]

    operations = [
        migrations.AddField(
            model_name='afterpickstaging',
            name='status',
            field=models.CharField(default='', max_length=30),
            preserve_default=False,
        ),
    ]
