# Generated by Django 3.2.5 on 2023-02-01 17:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('links_app', '0027_auto_20230201_1722'),
    ]

    operations = [
        migrations.CreateModel(
            name='Shipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Shipmentno', models.CharField(max_length=30)),
                ('orderno', models.CharField(max_length=30)),
                ('du', models.CharField(max_length=30)),
                ('shippeddate', models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]
