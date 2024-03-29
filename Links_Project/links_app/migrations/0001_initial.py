# Generated by Django 3.2.5 on 2022-10-19 22:41

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AsnLines',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asnno', models.CharField(max_length=30)),
                ('productcode', models.CharField(max_length=30)),
                ('description', models.CharField(max_length=128)),
                ('totalqty', models.IntegerField(default=0)),
                ('qtyreceived', models.IntegerField(default=0)),
                ('qtyshort', models.IntegerField(default=0)),
                ('qtyextra', models.IntegerField(default=0)),
                ('qtydamanged', models.IntegerField(default=0)),
                ('linestatus', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='BinContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('area', models.CharField(max_length=30)),
                ('bin', models.CharField(max_length=30)),
                ('active', models.CharField(max_length=30)),
                ('sut', models.CharField(max_length=30)),
                ('movementtype', models.CharField(max_length=30)),
                ('binsequence', models.IntegerField(default=0)),
                ('picksequenece', models.IntegerField(default=0)),
                ('productcode', models.CharField(max_length=30)),
                ('qty', models.IntegerField(default=0)),
                ('full', models.CharField(max_length=30)),
                ('allocated', models.CharField(max_length=30)),
                ('route', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Delivery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client', models.CharField(max_length=30)),
                ('asnno', models.CharField(max_length=30)),
                ('deliveryno', models.CharField(max_length=30)),
                ('type', models.CharField(max_length=30)),
                ('reference', models.CharField(max_length=30)),
                ('status', models.CharField(max_length=30)),
                ('asn_createdate', models.DateTimeField(blank=True, null=True)),
                ('delivery_createdate', models.DateTimeField(blank=True, null=True)),
                ('grn_date', models.DateTimeField(blank=True, null=True)),
                ('asn_createuser', models.CharField(max_length=30)),
                ('delivery_createuser', models.CharField(max_length=30)),
                ('assigned_user', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='ProductMaster',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client', models.CharField(max_length=30)),
                ('entity', models.CharField(max_length=5)),
                ('productcode', models.CharField(max_length=30)),
                ('description', models.CharField(max_length=50)),
                ('barcode', models.CharField(max_length=30)),
                ('costprice', models.FloatField(default=0)),
                ('saleprice', models.FloatField(default=0)),
                ('packqty', models.IntegerField(default=0)),
                ('uoi', models.IntegerField(default=0)),
                ('area', models.CharField(max_length=30)),
                ('sut', models.CharField(max_length=30)),
                ('movementtype', models.CharField(max_length=5)),
                ('status', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Routing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stagingtype', models.CharField(max_length=30)),
                ('holdingunit', models.CharField(max_length=30)),
                ('productcode', models.CharField(max_length=30)),
                ('qty', models.IntegerField(default=0)),
                ('targetbin_1', models.CharField(max_length=30)),
                ('targetbin_2', models.CharField(max_length=30)),
                ('targetbin_3', models.CharField(max_length=30)),
                ('status', models.CharField(max_length=30)),
            ],
        ),
    ]
