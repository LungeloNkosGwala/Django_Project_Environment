# Generated by Django 3.2.5 on 2022-11-22 17:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('links_app', '0006_rename_qtydamanged_asnlines_qtydamaged'),
    ]

    operations = [
        migrations.CreateModel(
            name='AfterPickStaging',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('area', models.CharField(max_length=30)),
                ('bin', models.CharField(max_length=30)),
                ('holdingvalue', models.IntegerField(default=0)),
                ('parent', models.CharField(max_length=30)),
                ('holdingunit', models.CharField(max_length=30)),
                ('productcode', models.CharField(max_length=30)),
                ('qty', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Customers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customercode', models.IntegerField(default=0, unique=True)),
                ('customername', models.CharField(max_length=50)),
                ('customertype', models.CharField(max_length=50)),
                ('account', models.IntegerField(default=0, unique=True)),
                ('routecode', models.IntegerField(default=0)),
                ('address', models.CharField(max_length=50)),
                ('emailaddress', models.EmailField(max_length=50, unique=True)),
                ('cellnumber', models.IntegerField(default=0)),
                ('telephonenumber', models.IntegerField(default=0)),
                ('vehicleaccesstype', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='OrderLines',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orderno', models.CharField(max_length=30)),
                ('productcode', models.CharField(max_length=30)),
                ('qtyordered', models.IntegerField(default=0)),
                ('qtyshipped', models.IntegerField(default=0)),
                ('qtybackorder', models.IntegerField(default=0)),
                ('qtycancelled', models.IntegerField(default=0)),
                ('linestatus', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='OrderManagement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('station', models.IntegerField(default=0)),
                ('position', models.IntegerField(default=0)),
                ('orderno', models.CharField(max_length=30)),
                ('productcode', models.CharField(max_length=30)),
                ('availableqty', models.IntegerField(default=0)),
                ('orderedqty', models.IntegerField(default=0)),
                ('pickedqty', models.IntegerField(default=0)),
                ('pickbin1', models.CharField(max_length=30)),
                ('pickbin2', models.CharField(max_length=30)),
                ('pickbin3', models.CharField(max_length=30)),
                ('allocated_user1', models.CharField(max_length=30)),
                ('allocated_user2', models.CharField(max_length=30)),
                ('allocated_user3', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Orders',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ordertype', models.CharField(max_length=30)),
                ('orderno', models.CharField(max_length=30)),
                ('reference', models.CharField(max_length=30)),
                ('customercode', models.IntegerField(default=0)),
                ('routecode', models.IntegerField(default=0)),
                ('linesordered', models.IntegerField(default=0)),
                ('linesshipped', models.IntegerField(default=0)),
                ('qtyordered', models.IntegerField(default=0)),
                ('qtyshipped', models.IntegerField(default=0)),
                ('linescancelled', models.IntegerField(default=0)),
                ('qtycancelled', models.IntegerField(default=0)),
                ('orderstatus', models.CharField(max_length=30)),
                ('processing_info', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='RouteCodes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('routecode', models.IntegerField(default=0)),
                ('country', models.CharField(max_length=30)),
                ('province', models.CharField(max_length=30)),
                ('area', models.CharField(max_length=30)),
                ('areatype', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department', models.CharField(max_length=30)),
                ('area', models.CharField(max_length=30)),
                ('station', models.CharField(max_length=30)),
                ('tool', models.CharField(max_length=30)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]