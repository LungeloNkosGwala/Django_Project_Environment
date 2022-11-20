from csv import unregister_dialect
from email import message
from poplib import POP3_PORT
from xml.dom import INVALID_MODIFICATION_ERR
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required,user_passes_test
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from links_app.models import ProductMaster, Routing, AsnLines,Delivery,BinContent, Transactions,Interrim
from django.db.models import Sum,Aggregate,Q,Max
from django.contrib import messages
from datetime import datetime
from django import forms
import pandas as pd
from random import random
from django.http import JsonResponse
import json
import plotly.express as px

# Create your views here.

asn_status = ["AsnCreated","DeliveryCreated","New","Inprogress","Closed","Complete"]
product_status = ['Active',"Discontinued","Inactive","Supercession"]
routing_status = ['AsnStaging',"BinRoute","StagingRoute","OrderStaging"]
placeholder = ['ASN','ASNNO','ORDER','ORDERNO']
linestatus = ["New","Inprogress","Closed","Damaged"]

def check_admin(user):
    return user.is_staff


def index(request):
    return render(request,"links_app/index.html")


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request,user)
                user_d = request.user
                #return HttpResponseRedirect(reverse("index"))
                return render(request,"links_app/index.html",{"user_d":user_d})
            else:
                return HttpResponse("Account Not active")
        else:
            print("Somone tried to login and failed")
            return HttpResponse("Invalid login details supplied")
    else:
        return render(request,'links_app/login.html')

@login_required
def register(request):
    avail_users = User.objects.all()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request,"links_app/index.html")
            #return HttpResponseRedirect(reverse("index"))
            #return redirect("lmini_app/index.html")
    else:
        form = UserCreationForm()
    return render(request, "links_app/systemcontrol/register.html",{"form":form,"avail_users":avail_users})



@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def verify_PM(request,productcode):
    verify = ProductMaster.objects.filter(Q(productcode=productcode)|Q(barcode=productcode)).first()
    return verify

def get_productcode(request,productcode):
    productcode = ProductMaster.objects.get(Q(barcode=productcode)|Q(productcode=productcode)).productcode
    return productcode

def verify_R(request,hu):
    verify = Routing.objects.filter(holdingunit=hu).first()
    return verify


def create_lines(request,asnno,data,linestatus):
    for i in data:
        el = AsnLines.objects.create(productcode=i.productcode)
        el.asnno = asnno
        el.description = ProductMaster.objects.get(productcode=i.productcode).description
        el.totalqty = i.qty
        el.linestatus = linestatus[0]
        el.save()





@login_required
def loadasn(request):
    user_d = request.user
    data = Routing.objects.all().filter(stagingtype=routing_status[0])
    if "stage" in request.POST:
        productcode = request.POST['productcode']
        qty = int(request.POST['qty'])

        if verify_PM(request,productcode) is None:
            print("None")
        else:
            productcode = get_productcode(request,productcode)
            stagingtype=routing_status[0]
            hu = placeholder[1]
            targetbin_1 = placeholder[0]
            Routing.routing(stagingtype,hu,productcode,qty,targetbin_1)
            return render(request,"links_app/inbound/loadasn.html",{"data":data})

    elif "create" in request.POST:
        data_1 = Routing.objects.filter(stagingtype=routing_status[0]).first()
        if data_1 is None:
            messages.warning(request, "No staged lines available to create Asn")
            return render(request,"links_app/inbound/loadasn.html",{"data":data})
        else:
            no = 10000
            asnno = "ASN"+str(no)
            verify = Delivery.objects.filter().first()
            asn_type = "Local"
            client = "Namlo"
            if verify is None:
                Delivery.create_asn(asnno,user_d,asn_type,client,asn_status)
                create_lines(request,asnno,data,linestatus)
                Routing.objects.filter(stagingtype=routing_status[0]).delete()
                messages.warning(request, "Asn created successfully")
                return render(request,"links_app/inbound/loadasn.html",{"user_d":user_d,"data":data})
            else:
                el = Delivery.objects.all().last().asnno
                el = int(el[3:])+1
                asnno = "ASN"+str(el)
                Delivery.create_asn(asnno,user_d,asn_type,client,asn_status)
                create_lines(request,asnno,data,linestatus)
                Routing.objects.filter(stagingtype=routing_status[0]).delete()
                messages.warning(request, "Asn created successfully")
                return render(request,"links_app/inbound/loadasn.html",{"user_d":user_d,"data":data})
    
    elif "execute" in request.POST:
        productcode = request.POST['delete']
        Routing.objects.filter(productcode=productcode,stagingtype=routing_status[0]).delete()
        messages.warning(request, "Part successfully remove from staging")
        return render(request,"links_app/inbound/loadasn.html",{"user_d":user_d,"data":data})

    else:
        pass

    return render(request,"links_app/inbound/loadasn.html",{"user_d":user_d,"data":data})


class CsvImportForm(forms.Form):
    csv_upload = forms.FileField(label=".txt File Upload")


def uploader(request, col_no):
    csv_file = request.FILES['csv_upload']

    if not csv_file.name.endswith(".txt"):
        messages.warning(request, "This file is invalid")
        return HttpResponseRedirect(request.path_info)

    file_data = csv_file.read().decode("utf-8")
    csv_data = file_data.split("\n")
    csv_data = csv_data[:-1]

    data = []

    for t in range(col_no):
        for x in csv_data:
            fields = x.split("\t")
            data.append(fields[t])

    pfep_ls = []
    for i in data:
        line = i.rstrip()
        pfep_ls.append(line)
    

    data = list()
    chunk_size = int(len(pfep_ls)/col_no)
    for i in range(0, len(pfep_ls), chunk_size):
        data .append(pfep_ls[i:i+chunk_size])


    df = pd.DataFrame(data).transpose()
    df.columns = df.iloc[0]
    df = df[1:]
    return df



@login_required
def pmupdate(request):
    if "upload_pm" in request.POST:
        col_no = 10
        df = uploader(request, col_no)
        for i in df.iterrows():
            ProductMaster.objects.filter(productcode = i[1][2]).delete()
            el = ProductMaster.objects.create(productcode=i[1][2])
            el.client = i[1][0]
            el.entity = i[1][1]
            el.description=i[1][3]
            el.barcode=i[1][4]
            el.costprice=i[1][5]
            el.saleprice=i[1][6]
            el.packqty=i[1][8]
            el.uoi=i[1][8]
            el.status=i[1][9]
            el.save()

        messages.warning(request, "Part successfully remove from staging")

    form = CsvImportForm()
    data = {'form':form}

    return render(request,"links_app/systemcontrol/pmupdate.html",data)

@login_required
def binupdate(request):
    count = 0
    if "upload_pm" in request.POST:
        col_no = 10
        df = uploader(request, col_no)
        Unsuccessful = []
        for i in df.iterrows():
            verify = BinContent.objects.filter(bin = i[1][1]).first()
            if verify is None:
                BinContent.bin_upload(i)
            else:
                qty = int(BinContent.objects.get(bin = i[1][1]).qty)
                if qty == 0:
                    BinContent.bin_upload(i)
                else:
                    Unsuccessful.append(i[1][1])

        count = len(Unsuccessful)


        messages.warning(request, "Bins successfully Created")

    form = CsvImportForm()
    data = {'form':form,"count":count}

    return render(request,"links_app/systemcontrol/binupdate.html",data)


@login_required
def createdelivery(request):
    user_d = request.user
    if "create" in request.POST:
        asnno = request.POST['asnno']
        ref = request.POST['ref']
        del_type = request.POST['type']

        verify = Delivery.objects.filter(asnno=asnno,type=del_type).first()
        if verify is None:
            print("Not successful")
            messages.warning(request,"ASN no. doesn't exist for this Delivery, please request an ASN creation")
            return render(request,"links_app/inbound/createdelivery.html",{"user_d":user_d})
        else:
            verify = Delivery.objects.filter(reference = ref).first()
            if verify is None:
                Delivery.objects.filter(asnno=asnno).update(deliveryno=str(asnno)+"_1", reference=ref, 
                                                            delivery_createdate=datetime.now(),
                                                            status=asn_status[1], delivery_createuser=str(user_d))
                dept_w = "Inbound"
                w_type = "CreateDelivery"
                origin = str(asnno)+"_1"
                productcode = ""
                sourcearea = del_type
                sourcebin = ""
                initialsoh = 0
                qty = 0
                resultsoh = 0
                targetbin = ""
                targetarea = "Delivery"
                holdingu = ""
                Transactions.transactions(dept_w,w_type,origin,productcode,sourcearea,sourcebin,initialsoh,qty,resultsoh,targetbin,targetarea,holdingu,user_d)
                messages.warning(request, "Delivery created successfully!")
                return render(request,"links_app/inbound/createdelivery.html",{"user_d":user_d})
            else:
                messages.warning(request,"Reference no. cannot be reused, please check for correct Delivery reference")
                return render(request,"links_app/inbound/createdelivery.html",{"user_d":user_d})


    return render(request,"links_app/inbound/createdelivery.html",{"user_d":user_d})


def check_user(request,assigned_user):
    verify = User.objects.filter(username=assigned_user).first()
    return verify

@login_required
def assignuser(request):
    user_d = request.user
    data = Delivery.objects.all().filter(Q(status=asn_status[1])|Q(status=asn_status[2])|Q(status=asn_status[3]))
    if "assign" in request.POST:
        asnno = request.POST['asnno']
        assigned_user = request.POST['assigned_user']
        verify = check_user(request,assigned_user)
        if verify is None:
            messages.warning(request, "Username doesn't exist")
        else:
            verify = Delivery.objects.filter(asnno=asnno).first()
            if verify is None:
                messages.warning(request, "ASN does not exist")
                return render(request,"links_app/inbound/assignuser.html",{"user_d":user_d,"data":data})
            else:
                index = asn_users(request,user_d)
                print(index)
                if index == 0 or index == 1 or index == 2:
                    print(index)
                    messages.warning(request, "Cannot assign User to another unClosed ASN")
                    return render(request,"links_app/inbound/assignuser.html",{"user_d":user_d,"data":data})
                elif index == 5:
                    cur_user = Delivery.objects.get(asnno=asnno).assigned_user1
                    if cur_user == " " or cur_user == "":
                        Delivery.objects.filter(asnno=asnno).update(assigned_user1=assigned_user)
                        messages.warning(request, "User successfully assigned to ASN")
                        return render(request,"links_app/inbound/assignuser.html",{"user_d":user_d,"data":data})
                    else:
                        cur_user = Delivery.objects.get(asnno=asnno).assigned_user2
                        if cur_user == " " or cur_user == "":
                            Delivery.objects.filter(asnno=asnno).update(assigned_user2=assigned_user)
                            messages.warning(request, "User successfully added onto ASN")
                            return render(request,"links_app/inbound/assignuser.html",{"user_d":user_d,"data":data})
                        else:
                            cur_user = Delivery.objects.get(asnno=asnno).assigned_user3
                            if cur_user == " " or cur_user == "":
                                Delivery.objects.filter(asnno=asnno).update(assigned_user3=assigned_user)
                                messages.warning(request, "User successfully added onto ASN")
                                return render(request,"links_app/inbound/assignuser.html",{"user_d":user_d,"data":data})
                            else:
                                messages.warning(request, "ASN cannot be assigned to more than 3 users")
                                return render(request,"links_app/inbound/assignuser.html",{"user_d":user_d,"data":data})
                else:
                    messages.warning(request, "Not successful")
                    return render(request,"links_app/inbound/assignuser.html",{"user_d":user_d,"data":data})

    elif "asnno_del" in request.POST:
        del_user = request.POST['del']
        asnno = request.POST['asnno_del']

        user_position = int(del_user[-1:])
        del_user = del_user[:-2]
        if user_position == 1:
            Delivery.objects.filter(asnno=asnno,assigned_user1=del_user).update(assigned_user1=" ")
            messages.warning(request,"User has been successfully removed from ASN")
            return render(request,"links_app/inbound/assignuser.html",{"user_d":user_d,"data":data})
        elif user_position == 2:
            Delivery.objects.filter(asnno=asnno,assigned_user2=del_user).update(assigned_user2=" ")
            messages.warning(request,"User has been successfully removed from ASN")
            return render(request,"links_app/inbound/assignuser.html",{"user_d":user_d,"data":data})
        elif user_position == 3:
            Delivery.objects.filter(asnno=asnno,assigned_user3=del_user).update(assigned_user3=" ")
            messages.warning(request,"User has been successfully removed from ASN")
            return render(request,"links_app/inbound/assignuser.html",{"user_d":user_d,"data":data})
        else:
            messages.warning(request,"Please select user to be deleted from ASN")
            return render(request,"links_app/inbound/assignuser.html",{"user_d":user_d,"data":data})

    else:
        return render(request,"links_app/inbound/assignuser.html",{"user_d":user_d,"data":data})

    return render(request,"links_app/inbound/assignuser.html",{"user_d":user_d,"data":data})

#def asn_users(request,user_d):
    #user1 = Delivery.objects.get(Q(status=asn_status[1])|Q(status=asn_status[2])|Q(status=asn_status[3]),assigned_user1=str(user_d)).assigned_user1
    #user2 = Delivery.objects.get(Q(status=asn_status[1])|Q(status=asn_status[2])|Q(status=asn_status[3]),assigned_user2=str(user_d)).assigned_user2
    #user3 = Delivery.objects.get(Q(status=asn_status[1])|Q(status=asn_status[2])|Q(status=asn_status[3]),assigned_user3=str(user_d)).assigned_user3
    #return user1,user2,user3

def asn_users(request,user_d):
    all_users = Delivery.objects.filter(Q(status=asn_status[1])|Q(status=asn_status[2])|Q(status=asn_status[3]))
    user1 = []
    user2 = []
    user3 = []
    for i in all_users:
        user1.append(i.assigned_user1)
        user2.append(i.assigned_user2)
        user3.append(i.assigned_user3)
    if str(user_d) in user1:
        index = 0
        return index
    elif str(user_d) in user2:
        index = 1
        return index
    elif str(user_d) in user3:
        index = 2
        return index
    else:
        index = 5
        return index



def user_postion(request,index,user_d):
    if index == 0:
        Data = Delivery.objects.all().filter(Q(status=asn_status[1])|Q(status=asn_status[2])|Q(status=asn_status[3]),assigned_user1=str(user_d))
        asnno_s = Delivery.objects.get(Q(status=asn_status[1])|Q(status=asn_status[2])|Q(status=asn_status[3]),assigned_user1=str(user_d)).asnno
        totalqty = list(AsnLines.objects.filter(asnno=asnno_s).aggregate(Sum('totalqty')).values())[0]
        qtyreceived = list(AsnLines.objects.filter(asnno=asnno_s).aggregate(Sum('qtyreceived')).values())[0]
        return Data,asnno_s,totalqty,qtyreceived
    elif index == 1:
        Data = Delivery.objects.all().filter(Q(status=asn_status[1])|Q(status=asn_status[2])|Q(status=asn_status[3]),assigned_user2=str(user_d))
        asnno_s = Delivery.objects.get(Q(status=asn_status[1])|Q(status=asn_status[2])|Q(status=asn_status[3]),assigned_user2=str(user_d)).asnno
        totalqty = list(AsnLines.objects.filter(asnno=asnno_s).aggregate(Sum('totalqty')).values())[0]
        qtyreceived = list(AsnLines.objects.filter(asnno=asnno_s).aggregate(Sum('qtyreceived')).values())[0]
        return Data,asnno_s,totalqty,qtyreceived
    elif index == 2:
        Data = Delivery.objects.all().filter(Q(status=asn_status[1])|Q(status=asn_status[2])|Q(status=asn_status[3]),assigned_user3=str(user_d))
        asnno_s = Delivery.objects.get(Q(status=asn_status[1])|Q(status=asn_status[2])|Q(status=asn_status[3]),assigned_user3=str(user_d)).asnno
        totalqty = list(AsnLines.objects.filter(asnno=asnno_s).aggregate(Sum('totalqty')).values())[0]
        qtyreceived = list(AsnLines.objects.filter(asnno=asnno_s).aggregate(Sum('qtyreceived')).values())[0]
        return Data,asnno_s,totalqty,qtyreceived
    else:
        Data = ""
        asnno_s = 0
        totalqty = 0
        qtyreceived = 0 
        return Data,asnno_s,totalqty,qtyreceived
        
def received(request,user_d,productcode,qty,type_rec,token,asnno_s,hu,Data,totalqty,qtyreceived,Data_r):
    if type_rec == "Good":
        #Loading Interrim
        area = "RCVAREA"
        binn = "RCVBIN1"
        parent = asnno_s
        Interrim.interrims(area,binn,parent,hu,productcode,qty)
        #Loading AsnLines
        source_qty = AsnLines.getQty(asnno_s,productcode)
        qtyreceived = int(qty)+int(source_qty)
        linestatuss = linestatus[1]
        AsnLines.loadLines(asnno_s,productcode,qtyreceived,linestatuss)
        #Loading Transactions
        dept_w = "Inbound"
        w_type = "Receiving"
        origin = asnno_s
        productcode = productcode
        sourcearea = "ASN"
        sourcebin = "Delivery"
        initialsoh = 0
        qty = int(qty)
        resultsoh = int(qty)
        targetbin = "RCVAREA"
        targetarea = "RCVBIN1"
        holdingu = hu
        Transactions.transactions(dept_w,w_type,origin,productcode,sourcearea,sourcebin,initialsoh,qty,resultsoh,targetbin,targetarea,holdingu,user_d)
        messages.warning(request,"Successfully Received part")
        return render(request,"links_app/inbound/receiveasn.html",{"user_d":user_d,"data":Data,"totalqty":totalqty,"qtyreceived":qtyreceived,"Data_r":Data_r})
    else:
        source_qty = AsnLines.getDamageQty(asnno_s,productcode)
        qtyreceived = int(qty)+int(source_qty)
        linestatuss = linestatus[1]
        AsnLines.loadDamageLines(asnno_s,productcode,qtyreceived,linestatuss)

        dept_w = "Inbound"
        w_type = "Receiving"
        origin = asnno_s
        productcode = productcode
        sourcearea = "ASN"
        sourcebin = "Delivery"
        initialsoh = 0
        qty = int(qty)
        resultsoh = int(qty)
        targetbin = "Damaged"
        targetarea = "Damaged"
        holdingu = hu
        Transactions.transactions(dept_w,w_type,origin,productcode,sourcearea,sourcebin,initialsoh,qty,resultsoh,targetbin,targetarea,holdingu,user_d)
        messages.warning(request,"Successfully Received part into Damages")
        return render(request,"links_app/inbound/receiveasn.html",{"user_d":user_d,"data":Data,"totalqty":totalqty,"qtyreceived":qtyreceived,"Data_r":Data_r})



@login_required
def receiveasn(request):
    user_d = request.user
    index = asn_users(request,user_d)
    Data,asnno_s,totalqty,qtyreceived = user_postion(request,index,user_d)
    Data_r = AsnLines.objects.all().filter(asnno=asnno_s)
    if Data == "":
        return render(request,"links_app/inbound/receiveasn.html")
    else:
        if "receive" in request.POST:
            productcode = request.POST['productcode']
            qty = request.POST['qty']
            type_rec = request.POST['type']
            hu = request.POST['hu']
            token = hu[:2]
            if (token == "HU" or "PL" or "TU") and len(hu) == 8:
                if (token == "HU" or "PL"):                                
                    verify = Transactions.objects.filter(holdingunit=hu).first()
                    if verify is None:
                        if verify_PM(request,productcode) is None:
                            messages.warning(request, "Productcode doesn't exist in PM, please update PM")
                            return render(request,"links_app/inbound/receiveasn.html",{"user_d":user_d,"data":Data,"totalqty":totalqty,"qtyreceived":qtyreceived,"Data_r":Data_r})
                        else:
                            productcode = get_productcode(request,productcode)
                            received(request,user_d,productcode,qty,type_rec,token,asnno_s,hu,Data,totalqty,qtyreceived,Data_r)  
                    else:
                        messages.warning(request,"This Holdingunit cannot be reused, please created another HU")
                        return render(request,"links_app/inbound/receiveasn.html",{"user_d":user_d,"data":Data,"totalqty":totalqty,"qtyreceived":qtyreceived,"Data_r":Data_r})
                else:
                    verify = Interrim.objects.filter(holdingunit=hu).first()
                    if verify is None:
                        if verify_PM(request,productcode) is None:
                            messages.warning(request, "Productcode doesn't exist in PM, please update PM")
                            return render(request,"links_app/inbound/receiveasn.html",{"user_d":user_d,"data":Data,"totalqty":totalqty,"qtyreceived":qtyreceived,"Data_r":Data_r})
                        else:
                            productcode = get_productcode(request,productcode)
                            received(request,user_d,productcode,qty,type_rec,token,asnno_s,hu,Data,totalqty,qtyreceived,Data_r)
                    else:
                        messages.warning(request,"TU already holding stock")
                        return render(request,"links_app/inbound/receiveasn.html",{"user_d":user_d,"data":Data,"totalqty":totalqty,"qtyreceived":qtyreceived,"Data_r":Data_r})
            else:
                messages.warning(request,"This is not valid Holdingunit, please use a valid HU")
                return render(request,"links_app/inbound/receiveasn.html",{"user_d":user_d,"data":Data,"totalqty":totalqty,"qtyreceived":qtyreceived,"Data_r":Data_r})
        elif "execute" in request.POST and "clear" in request.POST:
            productcode = request.POST['clear']
            verify = Transactions.objects.filter(workflowtype="Receiving",origin=asnno_s,productcode=productcode).first()
            if verify is None:
                messages.warning(request,"Receiving Transaction successfully reversed")
                return render(request,"links_app/inbound/receiveasn.html",{"user_d":user_d,"data":Data,"totalqty":totalqty,"qtyreceived":qtyreceived,"Data_r":Data_r})
            else:
                Interrim.objects.filter(parent = asnno_s,productcode=productcode).delete()
                AsnLines.objects.filter(asnno=asnno_s,productcode=productcode).update(qtyreceived=0)
                int_qty = list(Transactions.objects.filter(workflowtype="Receiving",origin=asnno_s,productcode=productcode).aggregate(Sum('qty')).values())[0]
                dept_w = "Inbound"
                w_type = "Reverse"
                origin = asnno_s
                productcode = productcode
                sourcearea = "RCVAREA"
                sourcebin = "RCVBIN1"
                initialsoh = int(int_qty)
                qty = int(int_qty)*-1
                resultsoh = 0
                targetbin = "Delivery"
                targetarea = "ASN"
                holdingu = ""
                Transactions.transactions(dept_w,w_type,origin,productcode,sourcearea,sourcebin,initialsoh,qty,resultsoh,targetbin,targetarea,holdingu,user_d)
                messages.warning(request,"Receiving Transaction successfully reversed")
                return render(request,"links_app/inbound/receiveasn.html",{"user_d":user_d,"data":Data,"totalqty":totalqty,"qtyreceived":qtyreceived,"Data_r":Data_r})
        elif "close" in request.POST:
            Delivery.objects.filter(asnno=asnno_s).update(status=asn_status[4])
            close_adj = AsnLines.objects.all().filter(asnno = asnno_s)
            for i in close_adj:
                if i.totalqty > i.qtyreceived:
                    AsnLines.objects.filter(asnno = asnno_s, productcode=i.productcode).update(qtyshort=int(i.totalqty-i.qtyreceived-i.qtydamaged))
                elif i.totalqty < i.qtyreceived:
                    AsnLines.objects.filter(asnno = asnno_s, productcode=i.productcode).update(qtyextra=int(i.qtyreceived- i.totalqty-i.qtydamaged))
                else:
                    pass
            dept_w = "Inbound"
            w_type = "CloseAsn"
            origin = asnno_s
            productcode = ""
            sourcearea = "RCVAREA"
            sourcebin = "RCVBIN1"
            initialsoh = 0
            qty = 0
            resultsoh = 0
            targetbin = ""
            targetarea = ""
            holdingu = ""
            Transactions.transactions(dept_w,w_type,origin,productcode,sourcearea,sourcebin,initialsoh,qty,resultsoh,targetbin,targetarea,holdingu,user_d)
            messages.warning(request,"ASN closed sucessfully")


    return render(request,"links_app/inbound/receiveasn.html",{"user_d":user_d,"data":Data,"totalqty":totalqty,"qtyreceived":qtyreceived,"Data_r":Data_r})


def load_route(request,targetbin_1,productcode,hu,r_area,r_sut,r_mtype,user_d):
    qty = int(Interrim.objects.get(holdingunit=hu).qty)

    createRoute = Routing.objects.create(holdingunit = hu)
    createRoute.productcode = productcode
    createRoute.stagingtype = "Routing"
    createRoute.qty = qty
    createRoute.targetbin_1 =str(targetbin_1)
    createRoute.save()

    BinContent.objects.filter(bin = targetbin_1).update(route="TRUE")

    dept_w = "Inbound"
    w_type = "createRoute"
    origin = ""
    sourcearea = "RCVAREA"
    sourcebin = "RCVBIN1"
    initialsoh = int(BinContent.objects.get(bin=str(targetbin_1)).qty)
    qty = int(Interrim.objects.get(holdingunit=hu).qty)
    resultsoh = 0
    targetbin = str(targetbin_1)
    targetarea = r_area
    holdingu = hu
    Transactions.transactions(dept_w,w_type,origin,productcode,sourcearea,sourcebin,initialsoh,qty,resultsoh,targetbin,targetarea,holdingu,user_d)
    Interrim.objects.filter(holdingunit=hu).delete()
    return qty
    



def create_route(request,productcode,user_d,hu):
    r_area = ProductMaster.objects.get(productcode = productcode).area
    r_sut = ProductMaster.objects.get(productcode = productcode).sut
    r_mtype = ProductMaster.objects.get(productcode = productcode).movementtype
    if r_area == "" or r_area == " " and r_mtype == "" or r_mtype == " ":
        messages.warning(request,"No PFEP setting exist for "+productcode+" ,please request PFEP setting")
        return render(request,"links_app/inbound/putaway.html",{"user_d":user_d})
    else:
        verify=Routing.objects.filter(holdingunit=hu).first()
        if verify is None:
            verify = BinContent.objects.filter(area = r_area,sut=r_sut,movementtype =r_mtype, full="FALSE",allocated="FALSE", route="FALSE",productcode=productcode).first()
            if verify is None:
                verify = BinContent.objects.filter(area = r_area,sut=r_sut,movementtype =r_mtype, full="FALSE",allocated="FALSE", route="FALSE",qty=0).first()
                if verify is None:
                    messages.warning(request, "Please change PFEP, no available bins for this productcode PFEP setting")
                    return render(request,"links_app/inbound/putaway.html",{"user_d":user_d})
                else:
                    bin_dict = BinContent.objects.filter(area = r_area,sut=r_sut,movementtype =r_mtype, full="FALSE",allocated="FALSE", route="FALSE",qty=0).values('bin')[0:1]
                    targetbin_1 = bin_dict[0].get('bin')
                    qty = load_route(request,targetbin_1,productcode,hu,r_area,r_sut,r_mtype,user_d)
                    messages.warning(request, "Route successfully created")
                    return render(request,"links_app/inbound/putaway.html",{"user_d":user_d,"targetbin_1":targetbin_1,"hu":hu,"qty":qty})
            else:
                bin_dict = BinContent.objects.filter(area = r_area,sut=r_sut,movementtype =r_mtype, full="FALSE",allocated="FALSE", route="FALSE",productcode=productcode).values('bin')[0:1]
                targetbin_1 = bin_dict[0].get('bin')
                qty = load_route(request,targetbin_1,productcode,hu,r_area,r_sut,r_mtype,user_d)
                messages.warning(request, "Route successfully created")
                return render(request,"links_app/inbound/putaway.html",{"user_d":user_d,"targetbin_1":targetbin_1,"hu":hu,"qty":qty})     
        else:
            messages.warning(request, "Item already has route")
            return render(request,"links_app/inbound/putaway.html",{"user_d":user_d})




def putaway_hu(request,hu,productcode,qty,bin,sourceqty,remaining_qty,nw_qty,user_d,TRUE_FALSE):
    #Into Bin Content
    BinContent.objects.filter(bin = bin).update(productcode=productcode, qty=nw_qty,full=TRUE_FALSE,route="FALSE")


    #Into WorkFlow
    dept_w = "Inbound"
    w_type = "Putaway"
    origin = ""
    sourcearea = "RCVAREA"
    sourcebin = "RCVBIN1"
    initialsoh = sourceqty
    resultsoh = nw_qty
    targetbin = bin
    targetarea = str(BinContent.objects.get(bin=bin).area)
    holdingu = hu
    Transactions.transactions(dept_w,w_type,origin,productcode,sourcearea,sourcebin,initialsoh,qty,resultsoh,targetbin,targetarea,holdingu,user_d)




def remainqty(request,hu,productcode,qty,bin,sourceqty,remaining_qty,nw_qty,user_d):
    if remaining_qty == 0:
        Routing.objects.get(holdingunit=hu).delete()
        TRUE_FALSE = "FALSE"
        putaway_hu(request,hu,productcode,qty,bin,sourceqty,remaining_qty,nw_qty,user_d,TRUE_FALSE)
        messages.success(request, "Part successfully Putaway")
        return render(request,"links_app/inbound/putaway.html",{"user_d":user_d})
    elif remaining_qty < 0:
        messages.success(request, "Your are binning more than available qty, please go check with your supervisor")
        return render(request,"links_app/inbound/putaway.html",{"user_d":user_d})
    else:
        Routing.objects.filter(holdingunit = hu).delete()
        TRUE_FALSE = "TRUE"
        putaway_hu(request,hu,productcode,qty,bin,sourceqty,remaining_qty,nw_qty,user_d,TRUE_FALSE)
        area = "RCVAREA"
        binn = "RCVBIN1"
        parent = "BinFull"
        qty = remaining_qty
        Interrim.interrims(area,binn,parent,hu,productcode,qty)
        messages.success(request, "Part successfully Putaway")
        return render(request,"links_app/inbound/putaway.html",{"user_d":user_d})



@login_required
def putaway(request):
    user_d = str(request.user)
    if "route" in request.POST and "hu" in request.POST:
        hu = request.POST['hu']
        verify = Routing.objects.filter(holdingunit=hu).first()
        if verify is None:
            verify = Interrim.objects.filter(holdingunit=hu).first()
            if verify is None:
                messages.warning(request,"HU either routed or is not available for routing")
                return render(request,"links_app/inbound/putaway.html",{"user_d":user_d})
            else:
                productcode = Interrim.objects.get(holdingunit=hu).productcode
                create_route(request,productcode,user_d,hu)
        else:
            messages.warning(request,"This HU is already routed")
            alll = Routing.objects.all().filter(holdingunit=hu)
            targetbin_1 = str(alll[0].targetbin_1)
            qty = str(alll[0].qty)
            return render(request,"links_app/inbound/putaway.html",{"user_d":user_d,"targetbin_1":targetbin_1,"hu":hu,"qty":qty}) 
    elif "hu" in request.POST and "productcode" in request.POST and "qty" in request.POST and "bin" in request.POST and "confirm" in request.POST and "type" in request.POST:
        hu = request.POST['hu']
        qty = int(request.POST['qty'])
        productcode = request.POST['productcode']
        bin = request.POST['bin']
        verify = verify_PM(request,productcode)
        if verify is None:
            messages.warning(request,"Productcode doesn't exist")
            return render(request,"links_app/inbound/putaway.html",{"user_d":user_d})
        else:
            productcode = get_productcode(request,productcode)
            verify = Routing.objects.filter(holdingunit=hu,productcode=productcode).first()
            if verify is None:
                messages.success(request, "HU or Productcode doesn't exist")
                return render(request,"links_app/inbound/putaway.html",{"user_d":user_d})
            else:
                verify = Routing.objects.filter(targetbin_1 = bin).first()
                if verify is None:
                    messages.success(request, "Cannot confirmed HU unto unRouted Bin, please route HU")
                    return render(request,"links_app/inbound/putaway.html",{"user_d":user_d})
                else:
                    verify = BinContent.objects.filter(bin=bin,productcode =productcode).first()
                    if verify is None:
                        #Remaning on Routing
                        remaining_qty = int(Routing.objects.get(holdingunit = hu).qty) - qty
                        sourceqty = 0
                        nw_qty = int(qty)
                        remainqty(request,hu,productcode,qty,bin,sourceqty,remaining_qty,nw_qty,user_d)                      
                    else:
                        remaining_qty = int(Routing.objects.get(holdingunit = hu).qty) - qty
                        sourceqty = int(BinContent.objects.get(bin=bin,productcode =productcode).qty)
                        nw_qty = int(sourceqty + qty)
                        remainqty(request,hu,productcode,qty,bin,sourceqty,remaining_qty,nw_qty,user_d)
        return render(request,"links_app/inbound/putaway.html",{"user_d":user_d})
    return render(request,"links_app/inbound/putaway.html",{"user_d":user_d})
        
            



@login_required
def pfep(request):
    user_d = request.user
    if "upload_pm" in request.POST:
        col_no = 4
        df = uploader(request, col_no)
        for i in df.iterrows():
            ProductMaster.objects.filter(productcode=i[1][0]).update(area=i[1][1],sut=i[1][2],movementtype=i[1][3])
        messages.warning(request, "PFEP sucessfully updated")

    form = CsvImportForm()
    data = {'form':form,"user_d":user_d}

    return render(request,"links_app/systemcontrol/pfep.html",data)


@login_required
def asn_inquire(request):
    user_d = request.user
    if "asnno" in request.GET:
        query = request.GET.get('asnno')
        print()
        verify = Delivery.objects.filter(asnno=query).first()
        if verify is None:
            return render(request,"links_app/inquire/asn_inquire.html",{"user_d":user_d})
        else:
            data = Delivery.objects.all().filter(asnno=query)
            sel_data = AsnLines.objects.all().filter(asnno=query)
            return render(request,"links_app/inquire/asn_inquire.html",{"user_d":user_d,"data":data,"sel_data":sel_data})
    return render(request,"links_app/inquire/asn_inquire.html",{"user_d":user_d})



def transactions(request):
    user_d = request.user
    query = request.GET.get('search')
    sd = request.GET.get("from")
    ed = request.GET.get("to")
    
    if ed == "" and sd == "":
        ed = "2060-12-31"
        sd = "2020-12-31"
    elif ed == "":
        ed = "2060-12-31"
    elif sd == "":
        sd = "2020-12-31"
    else:
        pass


    verify = ProductMaster.objects.filter(Q(productcode=query)|Q(barcode=query)).first()
    if verify is None:
        verify = Transactions.objects.filter(Q(holdingunit=query)|Q(workflowtype=query)|Q(origin=query)|Q(user_transactions=query))
        if verify is None:
            return render(request,"links_app/inquire/transactions.html",{"user_d":user_d})
        else:
            data = Transactions.objects.all().filter(Q(holdingunit=query)|Q(workflowtype=query)|Q(origin=query)|Q(user_transactions=query), transactiondate__range=[sd, ed])
            return render(request,"links_app/inquire/transactions.html",{"data":data,"user_d":user_d})
    else:
        productcode = str(ProductMaster.objects.get(Q(productcode=query)|Q(barcode=query)).productcode)
        data = Transactions.objects.all().filter(productcode=productcode,transactiondate__range=[sd, ed])
        return render(request,"links_app/inquire/transactions.html",{"data":data,"user_d":user_d})
    
    return render(request,"links_app/inquire/transactions.html")


def create_pickingslip(request):
    data = Routing.objects.all().filter(stagingtype=routing_status[3])
    user_d = request.user
    if "search" in request.GET:
        query = request.GET.get('asnno')
        productcode=ProductMaster.objects.filter(Q(productcode__icontains=query))
        return render(request,"links_app/outbound/create_pickingslip.html",{"user_d":user_d,"productcode":productcode,"data":data})
    elif "stage" in request.GET and "sel" in request.GET and "qty" in request.GET:
        qty = int(request.GET.get('qty'))
        productcode = request.GET.get("sel")
        stagingtype=routing_status[3]
        hu = placeholder[3]
        targetbin_1 = placeholder[2]
        Routing.routing(stagingtype,hu,productcode,qty,targetbin_1)
        messages.warning(request,"Line staged successfully")
        return render(request,"links_app/outbound/create_pickingslip.html",{"user_d":user_d,"data":data})
    elif "execute" in request.GET and "selected" in request.GET:
        productcode = request.GET.get("selected")
        Routing.objects.filter(productcode=productcode,stagingtype=routing_status[3]).delete()
        messages.warning(request, "Part successfully remove from staging")
        return render(request,"links_app/outbound/create_pickingslip.html",{"user_d":user_d,"data":data})

    return render(request,"links_app/outbound/create_pickingslip.html",{"user_d":user_d,"data":data})


def product_inquire(request):
    user_d = request.user
    if "search" in request.POST:
        productcode= request.POST['productcode']
        verify = verify_PM(request,productcode)
        if verify is None:
            messages.warning(request,"links_app/inquire/product_inquire.html",{"user_d":user_d})
            return render(request,"links_app/inquire/product_inquire.html",{"user_d":user_d})
        else:
            data = BinContent.objects.filter(productcode=productcode).values('productcode').annotate(total = Sum('qty'))
            data1 = ProductMaster.objects.all().filter(productcode=productcode)
            print("data")
            return render(request,"links_app/inquire/product_inquire.html",{"user_d":user_d,"data":data,"data1":data1})
    return render(request,"links_app/inquire/product_inquire.html",{"user_d":user_d})




def analytics(request):
    user_d = request.user
    data = Transactions.objects.filter(workflowtype="Receiving").values("productcode").annotate(total = Sum('qty'))
    data = BinContent.objects.filter().values('productcode').annotate(total = Sum('qty'))

    fig = px.bar(
        x = [c.get('productcode') for c in data],
        y = [c.get('total') for c in data],
        text = [c.get('total') for c in data], 
    )

    fig.update_layout(title = "StockonHand",
                    yaxis_title = "Qty",
                    xaxis_title = "Productcode")


    chart = fig.to_html()
    return render(request,"links_app/reports/analytics.html",{"user_d":user_d,"data":data,"chart":chart})


"""def get_data(request, *args,**kwargs):
    data = Transactions.objects.filter(workflowtype="Receiving").values("productcode").annotate(total = Sum('qty'))
    return JsonResponse"""