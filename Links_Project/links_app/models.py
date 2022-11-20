from email.policy import default
from django.db import models
from django.forms import CharField, IntegerField
from django.contrib.auth.models import User
from datetime import datetime

# Create your models here.
class ProductMaster(models.Model):
    client = models.CharField(max_length=30)
    entity = models.CharField(max_length=5)
    productcode=models.CharField(max_length=30)
    description=models.CharField(max_length=50)
    barcode = models.CharField(max_length=30)
    costprice = models.FloatField(default = 0)
    saleprice = models.FloatField(default = 0)
    packqty = models.IntegerField(default=0)
    uoi = models.IntegerField(default=0)
    area = models.CharField(max_length=30)
    sut = models.CharField(max_length=30)
    movementtype = models.CharField(max_length=5)
    status = models.CharField(max_length=30)


class Delivery(models.Model):
    client = models.CharField(max_length=30)
    asnno = models.CharField(max_length=30)
    deliveryno = models.CharField(max_length=30)
    type = models.CharField(max_length=30)
    reference = models.CharField(max_length=30)
    invoice = models.CharField(max_length=30)
    status = models.CharField(max_length=30)
    asn_createdate = models.DateTimeField(null=True, blank=True)
    delivery_createdate = models.DateTimeField(null=True, blank=True)
    grn_date = models.DateTimeField(null=True, blank=True)
    asn_createuser = models.CharField(max_length=30)
    delivery_createuser = models.CharField(max_length=30)
    assigned_user1 = models.CharField(max_length=30)
    assigned_user2 = models.CharField(max_length=30)
    assigned_user3 = models.CharField(max_length=30)


    @classmethod
    def create_asn(self,asnno,user_d,asn_type,client,asn_status):
        el = Delivery.objects.create(asnno = asnno)
        el.client = client
        el.type = asn_type
        el.status = asn_status[0]
        el.asn_createdate = datetime.now()
        el.asn_createuser = str(user_d)
        el.save()

class Routing(models.Model):
    stagingtype = models.CharField(max_length=30)
    holdingunit = models.CharField(max_length=30)
    productcode = models.CharField(max_length=30)
    qty = models.IntegerField(default = 0)
    targetbin_1 = models.CharField(max_length=30)
    targetbin_2 = models.CharField(max_length=30)
    targetbin_3 = models.CharField(max_length=30)
    status = models.CharField(max_length=30)

    

    @classmethod
    def routing(self, stagingtype,hu,productcode,qty,targetbin_1):
        el = Routing.objects.create(stagingtype=stagingtype)
        el.holdingunit = hu
        el.productcode = productcode
        el.qty = qty
        el.targetbin_1 = targetbin_1
        el.save()

class AsnLines(models.Model):
    asnno = models.CharField(max_length=30)
    productcode = models.CharField(max_length=30)
    description = models.CharField(max_length=128)
    totalqty = models.IntegerField(default = 0)
    qtyreceived = models.IntegerField(default = 0)
    qtyshort = models.IntegerField(default = 0)
    qtyextra = models.IntegerField(default = 0)
    qtydamaged = models.IntegerField(default = 0)
    linestatus = models.CharField(max_length = 30)

    @classmethod
    def loadLines(self,asnno_s,productcode,qtyreceived,linestatuss):
        AsnLines.objects.filter(asnno=asnno_s,productcode=productcode).update(qtyreceived=qtyreceived,linestatus=linestatuss)

    @classmethod
    def loadDamageLines(self,asnno_s,productcode,qtyreceived,linestatuss):
        AsnLines.objects.filter(asnno=asnno_s,productcode=productcode).update(qtydamanged=qtyreceived,linestatus=linestatuss)
    
    @classmethod
    def getQty(self,asnno_s,productcode):
        source_qty = int(AsnLines.objects.get(asnno=asnno_s,productcode=productcode).qtyreceived)
        return source_qty

    @classmethod
    def getDamageQty(self,asnno_s,productcode):
        source_qty = int(AsnLines.objects.get(asnno=asnno_s,productcode=productcode).qtydamanged)
        return source_qty



class BinContent(models.Model):
    area = models.CharField(max_length=30)
    bin = models.CharField(max_length=30)
    active = models.CharField(max_length=30)
    sut = models.CharField(max_length=30)
    movementtype = models.CharField(max_length=30)
    binsequence = models.IntegerField(default = 0)
    picksequenece = models.IntegerField(default = 0)
    productcode = models.CharField(max_length=30)
    qty = models.IntegerField(default = 0)
    full = models.CharField(default = "False", max_length=30)
    allocated = models.CharField(default = "False",max_length=30)
    route = models.CharField(default = "False",max_length=30)


    @classmethod
    def bin_upload(self,i):
        BinContent.objects.filter(bin = i[1][1]).delete()
        el = BinContent.objects.create(bin=i[1][1])
        el.area = i[1][0]
        el.active= i[1][2]
        el.sut=i[1][3]
        el.binsequence=i[1][4]
        el.picksequenece=i[1][5]
        el.movementtype=i[1][6]
        el.full = i[1][7]
        el.allocated = i[1][8]
        el.route = i[1][9]
        el.save()


class Transactions(models.Model):
    dept_workflow = models.CharField(max_length=30)
    workflowtype = models.CharField(max_length=30)
    origin = models.CharField(max_length=30)
    productcode = models.CharField(max_length=30)
    sourcearea = models.CharField(max_length=30)
    sourcebin = models.CharField(max_length=30)
    Initial_SOH = models.IntegerField(default=0)
    qty = models.IntegerField(default=0)
    Result_SOH = models.IntegerField(default=0)
    targetbin = models.CharField(max_length=30)
    targetarea = models.CharField(max_length=30)
    holdingunit = models.CharField(max_length=30)
    transactiondate = models.DateTimeField(null=True, blank=True)
    user_transactions = models.CharField(max_length=30)


    @classmethod
    def transactions(self,dept_w,w_type,origin,productcode,sourcearea,sourcebin,initialsoh,qty,resultsoh,targetbin,targetarea,holdingu,user_d):
        el = Transactions.objects.create(productcode=productcode)
        el.dept_workflow = dept_w
        el.workflowtype = w_type
        el.origin = origin
        el.sourcearea=sourcearea
        el.sourcebin = sourcebin
        el.Initial_SOH = initialsoh
        el.qty = qty
        el.Result_SOH = resultsoh
        el.targetarea = targetarea
        el.targetbin = targetbin
        el.holdingunit = holdingu
        el.transactiondate = datetime.now()
        el.user_transactions = str(user_d)
        el.save()

class Interrim(models.Model):
    area = models.CharField(max_length=30)
    bin = models.CharField(max_length=30)
    parent = models.CharField(max_length=30)
    holdingunit = models.CharField(max_length=30)
    productcode = models.CharField(max_length=30)
    qty = models.IntegerField(default=0)
    createdate = models.DateTimeField(null=True, blank=True)

    @classmethod
    def interrims(self,area,binn,parent,hu,productcode,qty):
        el = Interrim.objects.create(productcode=productcode)
        el.area = area
        el.bin = binn
        el.parent = parent
        el.holdingunit = hu
        el.qty = qty
        el.createdate = datetime.now()
        el.save()

class OrderLines(models.Model):
    orderno = models.CharField(max_length=30)
    productcode = models.CharField(max_length=30)
    holdingunit = models.CharField(max_length=30)
    qtyordered = models.IntegerField(default = 0)
    qtyshipped = models.IntegerField(default = 0)
    qtybackorder = models.IntegerField(default = 0)
    qtycancelled = models.IntegerField(default = 0)
    linestatus = models.CharField(max_length = 30)

class Orders(models.Model):
    ordertype = models.CharField(max_length=30)
    orderno = models.CharField(max_length=30)
    reference = models.CharField(max_length=30)
    customercode = models.IntegerField(default = 0)
    routecode = models.IntegerField(default = 0)
    linesordered = models.IntegerField(default = 0)
    linesshipped = models.IntegerField(default = 0)
    qtyordered = models.IntegerField(default = 0)
    qtyshipped = models.IntegerField(default = 0)
    linescancelled = models.IntegerField(default = 0)
    qtycancelled = models.IntegerField(default = 0)
    totalcost = models.FloatField(default = 0)
    totalsale = models.FloatField(default = 0)
    orderstatus = models.CharField(max_length = 30)

    #To be continiued 



class Customers(models.Model):
    customercode = models.IntegerField(default = 0, unique=True)
    customername = models.CharField(max_length=50)
    customertype = models.CharField(max_length=50)
    account = models.IntegerField(default = 0, unique=True)
    routecode = models.IntegerField(default = 0)
    address = models.CharField(max_length=50)
    emailaddress = models.EmailField(max_length = 50, unique=True)
    cellnumber = models.IntegerField(default = 0)
    telephonenumber = models.IntegerField(default = 0)
    vehicleaccesstype = models.CharField(max_length=30)


class RouteCodes(models.Model):
    routecode = models.IntegerField(default = 0)
    country = models.CharField(max_length=30)
    province = models.CharField(max_length=30)
    area = models.CharField(max_length=30)
    areatype = models.CharField(max_length=30)

class AfterPickStaging(models.Model):
    area = models.CharField(max_length=30)
    bin = models.CharField(max_length=30)
    holdingvalue = models.IntegerField(default=0)
    parent = models.CharField(max_length=30)
    holdingunit = models.CharField(max_length=30)
    productcode = models.CharField(max_length=30)
    qty = models.IntegerField(default=0)


class OrderManagement(models.Model):
    orderno = models.CharField(max_length=30)
    

    #to be continued
