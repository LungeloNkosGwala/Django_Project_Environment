# Generated by Django 3.2.5 on 2023-01-14 19:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('links_app', '0021_auto_20230114_1829'),
    ]

    operations = [
        migrations.RenameField(
            model_name='afterpickstaging',
            old_name='holdingunit',
            new_name='holdingunit1',
        ),
        migrations.RenameField(
            model_name='afterpickstaging',
            old_name='parent',
            new_name='holdingunit2',
        ),
        migrations.RenameField(
            model_name='afterpickstaging',
            old_name='productcode',
            new_name='holdingunit3',
        ),
        migrations.RemoveField(
            model_name='afterpickstaging',
            name='qty',
        ),
    ]
