# Generated by Django 3.2.5 on 2022-11-29 20:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('links_app', '0010_auto_20221125_2352'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordermanagement',
            name='allocated',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='ordermanagement',
            name='call',
            field=models.CharField(default='', max_length=30),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='ordermanagement',
            name='station',
            field=models.CharField(max_length=30),
        ),
    ]