# Generated by Django 3.2.5 on 2022-11-04 16:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('links_app', '0005_auto_20221103_1825'),
    ]

    operations = [
        migrations.RenameField(
            model_name='asnlines',
            old_name='qtydamanged',
            new_name='qtydamaged',
        ),
    ]
