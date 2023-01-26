from django.shortcuts import render
from django.contrib.auth import authenticate, login,logout
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from links_app.models import ProductMaster, Routing, AsnLines,Delivery,BinContent, Transactions,Interrim,RouteCodes
from links_app.models import AllocateCapacity,Customers,Orders,OrderLines,Employee,Orders,OrderManagement,OrderSchedule,AfterPickStaging
from django.db.models import Sum,Aggregate,Q,Max,Count
from django.contrib import messages
from datetime import datetime
from django import forms
import pandas as pd
import plotly.express as px
import xlwt

# Create your views here.

asn_status = ["AsnCreated","DeliveryCreated","New","Inprogress","Closed","Complete"]
product_status = ['Active',"Discontinued","Inactive","Supercession"]
routing_status = ['AsnStaging',"BinRoute","StagingRoute","OrderStaging"]
placeholder = ['ASN','ASNNO','ORDER','ORDERNO']
linestatus = ["New","Inprogress","Closed","Damaged","Picked",'Packed','Shipped',"BackOrder"]
orderstatus = ['New','Allocated','Picking','PickStaging','Packing','Routecage',"Shipped"]

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
            Routing.routing(stagingtype,hu,productcode,qty,targetbin_1,user_d)
            messages.warning(request, "Part successfully staged")
            #return render(request,"links_app/inbound/loadasn.html",{"data":data})

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
        #return render(request,"links_app/inbound/loadasn.html",{"user_d":user_d,"data":data})

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
    BinContent.objects.filter(bin = bin).update(productcode=productcode, qty=nw_qty,avail_qty=nw_qty,full=TRUE_FALSE,route="FALSE")


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
        qty = request.POST['qty']
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


def bin_inquire(request):
    user_d = request.user

    if "bin" in request.GET:
        query = request.GET.get("bin")
        verify = BinContent.objects.filter(bin=query).first()

        if verify is None:
            return render(request,"links_app/inquire/bin_inquire.html",{"user_d":user_d})
        else:
            data = BinContent.objects.all().filter(bin=query)
            return render(request,"links_app/inquire/bin_inquire.html",{"user_d":user_d,"data":data})
    elif "productcode" in request.GET:
        productcode = request.GET.get("productcode")

        verify = verify_PM(request,productcode)
        if verify is None:
            return render(request,"links_app/inquire/bin_inquire.html",{"user_d":user_d})
        else:
            data1 = BinContent.objects.all().filter(productcode=productcode)
            return render(request,"links_app/inquire/bin_inquire.html",{"user_d":user_d,"data1":data1})
    return render(request,"links_app/inquire/bin_inquire.html",{"user_d":user_d})




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


def base_system(request):
    return render(request,"links_app/systemcontrol/base_system.html")

def routecode_update(request):
    if "upload_pm" in request.POST:
        col_no = 4
        df = uploader(request, col_no)
        for i in df.iterrows():
            RouteCodes.objects.filter(routecode = i[1][0]).delete()
            el = RouteCodes.objects.create(routecode=i[1][0])
            el.country = i[1][1]
            el.province = i[1][2]
            el.area=i[1][3]
            el.save()

        messages.warning(request, "Route Codes succesfully loaded")

    form = CsvImportForm()
    data = {'form':form}

    return render(request, "links_app/systemcontrol/systemmaintenance/routecode_update.html", data)


def cust_routecode(request):
    data = RouteCodes.objects.all()
    sel = ["cust_name","accountno","street","surburb",'city','postalcode','emailad','cellno','telno','routecode']
    if sel[0] in request.POST and sel[2] in request.POST and sel[4] in request.POST and sel[6] in request.POST and sel[9] in request.POST and "create" in request.POST:
        verify = Customers.objects.filter().first()
        if verify is None:
            intial = 100
        else:
            intial = int(Customers.objects.all().last().customercode)+1

        verify = Customers.objects.filter(Q(emailaddress=request.POST[sel[6]])|Q(account=int(request.POST[sel[1]]))).first()
        if verify is None:
            el = Customers.objects.create(customercode=intial,account=int(request.POST[sel[1]]),emailaddress=request.POST[sel[6]])
            el.address = str(request.POST[sel[2]])+"/"+str(request.POST[sel[3]])+"/"+str(request.POST[sel[4]])+"/" +str(request.POST[sel[5]])
            el.cellnumber = str(request.POST[sel[7]])
            el.telephonenumber = str(request.POST[sel[8]])
            el.routecode = int(request.POST[sel[9]])
            el.customername = str(request.POST[sel[0]])
            el.customertype='Local'
            el.save()
            print("Successlly excuted")
            messages.warning(request,"Customer details Entered successfully")
            return render(request, "links_app/systemcontrol/systemmaintenance/cust_routecode.html",{"data":data})
        else:
            messages.warning(request,"Email or Account is already in Use")
            return render(request, "links_app/systemcontrol/systemmaintenance/cust_routecode.html",{"data":data})


    return render(request, "links_app/systemcontrol/systemmaintenance/cust_routecode.html",{"data":data})

def loadorderlines(request,orderno,user_d):
    for i in Routing.objects.all().filter(stagingtype=routing_status[3],route_user=str(user_d)):
        el = OrderLines.objects.create(productcode = i.productcode)
        el.orderno = orderno
        el.qtyordered = i.qty
        el.linestatus = linestatus[0]
        el.save()

def create_pickingslip(request):
    user_d = request.user
    data = Routing.objects.all().filter(stagingtype=routing_status[3],route_user=str(user_d))
    Cust = Customers.objects.all()
    if "search" in request.GET:
        query = request.GET.get('asnno')
        productcode=ProductMaster.objects.filter(Q(productcode__icontains=query))
        return render(request,"links_app/outbound/create_pickingslip.html",{"user_d":user_d,"productcode":productcode,"data":data,"Cust":Cust})
    elif "stage" in request.GET and "sel" in request.GET and "qty" in request.GET:
        if int(Routing.objects.filter(stagingtype=routing_status[3],route_user=str(user_d)).count()) == 20:
            messages.warning(request,"You can only have 20 productcodes per Order, please submit and load another Order")
            return render(request,"links_app/outbound/create_pickingslip.html",{"user_d":user_d,"data":data,"Cust":Cust})
        else:
            qty = int(request.GET.get('qty'))
            productcode = request.GET.get("sel")
            stagingtype=routing_status[3]
            hu = placeholder[3]
            targetbin_1 = placeholder[2]
            Routing.routing(stagingtype,hu,productcode,qty,targetbin_1,user_d)

            messages.warning(request,"Line staged successfully")
            return render(request,"links_app/outbound/create_pickingslip.html",{"user_d":user_d,"data":data,"Cust":Cust})
    elif "execute" in request.GET and "selected" in request.GET:
        productcode = request.GET.get("selected")
        Routing.objects.filter(productcode=productcode,stagingtype=routing_status[3],route_user=str(user_d)).delete()
        messages.warning(request, "Part successfully remove from staging")
        return render(request,"links_app/outbound/create_pickingslip.html",{"user_d":user_d,"data":data,"Cust":Cust})

    elif "create" in request.GET:
        verify = Routing.objects.filter(stagingtype=routing_status[3],route_user=str(user_d)).first()
        if verify is None:
            messages.warning(request, "There are not productcodes staged to order creations")
            return render(request,"links_app/outbound/create_pickingslip.html",{"user_d":user_d,"data":data,"Cust":Cust})
        else:
            customercode = request.GET.get("customercode")
            routecode = int(customercode[3:])
            customercode = int(customercode[:3])
            ordertype = Customers.objects.get(customercode=customercode).customertype
            order_status = orderstatus[0]
            processing_info = 'NormalOrder'
            linesordered = int(Routing.objects.filter(stagingtype=routing_status[3],route_user=str(user_d)).count())
            qtyordered = int(Routing.objects.filter(stagingtype=routing_status[3],route_user=str(user_d)).aggregate(Sum('qty'))["qty__sum"])
            orderno = Orders.loadorder(ordertype,customercode,routecode,linesordered,qtyordered,order_status,processing_info)
            loadorderlines(request,orderno,user_d)
            Routing.objects.filter(stagingtype=routing_status[3],route_user=str(user_d)).delete()
            messages.warning(request, "Orderno has been successfully been created")
            return render(request,"links_app/outbound/create_pickingslip.html",{"user_d":user_d,"data":data,"Cust":Cust})


    return render(request,"links_app/outbound/create_pickingslip.html",{"user_d":user_d,"data":data,"Cust":Cust})


def product_inquire(request):
    user_d = request.user
    if "search" in request.POST:
        productcode= request.POST['productcode']
        verify = verify_PM(request,productcode)
        if verify is None:
            messages.warning(request,"productcode doesn't exist")
            return render(request,"links_app/inquire/product_inquire.html",{"user_d":user_d})
        else:
            data = BinContent.objects.filter(productcode=productcode).values('productcode').annotate(total = Sum('qty'))
            data1 = ProductMaster.objects.all().filter(productcode=productcode)
            print("data")
            return render(request,"links_app/inquire/product_inquire.html",{"user_d":user_d,"data":data,"data1":data1})
    return render(request,"links_app/inquire/product_inquire.html",{"user_d":user_d})


def rep_inbound(request):
    user_d = request.user
    if "download" in request.GET:
        query = request.GET.get('type')
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

        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="{}.xls"'.format(query)

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet(query) # this will make a sheet named Users Data

        # Sheet header, first row
        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = ['WorkflowType', 'Productcode', 'Qty', 'Targetbin', 'HoldingUnit','user_transactions']

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style) # at 0 row 0 column 


        # Sheet body, remaining rows
        font_style = xlwt.XFStyle()

        rows = list(Transactions.objects.all().filter(workflowtype=query,transactiondate__range=[sd, ed]).values_list('workflowtype', 'productcode', 'qty', 'targetbin',"holdingunit","user_transactions"))
        


                  
        for row in rows:
            row_num += 1
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)

        
        wb.save(response)

        return response
    return render(request,"links_app/reports/rep_inbound.html",{"user_d":user_d})


def analytics(request):
    user_d = request.user
    data = Transactions.objects.filter(workflowtype="Receiving").values("productcode").annotate(total = Sum('qty'))
    data = BinContent.objects.filter().values('productcode').annotate(total = Sum('qty'))
    print(data)

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


dept = {"0":"Select Dept",'1': 'Outbound', '2': 'Inbound', '3': 'Inventory', '4': 'Technical'}
area = {"0":"Select Area",'1': 'Picker', '2': 'Packer', '3': 'Shipper', '4': 'Receiver', '5': 'Binner', '6': 'Counter', '7': 'Technical',"8":"PalletP"}
def user_management(request):
    user_d = request.user
    if "search" in request.GET:
        query = request.GET.get('asnno')
        employees=User.objects.filter(Q(username__icontains=query))
        return render(request,"links_app/systemcontrol/systemmaintenance/user_management.html",{"user_d":user_d,'employees':employees})
    elif "select" in request.GET and "sel" in request.GET:
        sel_user = request.GET.get("sel")
        user_s = int(User.objects.get(username=str(sel_user)).id)
        user_s = Employee.objects.all().filter(user_id=user_s)
        return render(request,"links_app/systemcontrol/systemmaintenance/user_management.html",{"user_d":user_d,"user_s":user_s,"sel_user":sel_user,"dept":dept,"area":area})
    elif "update" in request.GET and "dept" in request.GET and "area" in request.GET:
        selected_user = request.GET.get("selected_user")
        sel_dept = request.GET.get("dept")
        sel_area = request.GET.get("area")
        
        if selected_user is None or sel_dept == "Select Dept" or sel_area == "Select Area" or selected_user == "Lungelo":
            messages.warning(request,"Invalid Selection, check your input correctly")
        else:
            user_sel = int(User.objects.get(username=selected_user).id)
            verify = Employee.objects.filter(user_id=user_sel).first()
            if verify is None:
                el = Employee.objects.create(user_id=user_sel)
                el.department = sel_dept
                el.area = sel_area
                el.save()
                messages.warning(request,"User details updated successfully")
            else:
                Employee.objects.filter(user_id=user_sel).update(department=sel_dept,area=sel_area)
                messages.warning(request,"User details updated successfully")

    return render(request,"links_app/systemcontrol/systemmaintenance/user_management.html",{"user_d":user_d})
    

def get_pickers(request):
    #Function to allocate users to picksbins
    picker_list = list(Employee.objects.filter(department="Outbound",area="Picker").values_list('user_id'))
    
    p_id = []
    p_name = []

    for i in picker_list:
        p_id.append(i[0])
        a = str(User.objects.get(id=i[0]).username)
        p_name.append(a)

    # Get Pallet Pickers
    pallet_list = list(Employee.objects.filter(department="Outbound",area="PalletP").values_list('user_id'))

    pp_id = []
    pp_name = []
    for i in pallet_list:
        pp_id.append(i[0])
        a = str(User.objects.get(id=i[0]).username)
        pp_name.append(a)

    return p_id,p_name,pp_id,pp_name


def get_bins(request):
    pb = ["pickbin1",'pickbin2','pickbin3']
    
    bins = []
    binss = []
    sequence = []
    area = []
    r = 1
    for t in pb:
        call = list(OrderManagement.objects.filter(orderedqty__gt=0).values_list(t))
        if call is None:
            pass
        else:
            for i in call:
                if i[0] == "NA":
                    pass
                else:
                    bins.append(i[0])
                    binss.append(i[0])
                    print(i[0])
                    a = int(BinContent.objects.get(bin=i[0]).binsequence)
                    b = str(BinContent.objects.get(bin=i[0]).area)
                    sequence.append(a)
                    area.append(b)
        binss.append("Stop_"+str(r))
        r= r+1
    
    res = []
    for i in binss:
        if i not in res:
            res.append(i)

    df = {"area":area,"bins":bins,"sequence":sequence}
    df = pd.DataFrame(df, columns={"area","bins",'sequence'})

    #Pallet Bins
    pallet = df[df['area']=="Pallet"]

    mezz = df[~df.area.isin(['Pallet'])]

    mezz.drop_duplicates(subset="bins", keep ='last', inplace=True)

    palletl = list(pallet['bins'])

    res = [i for i in res if i not in palletl]

    x1 = res.index("Stop_1")
    bin1 = res[:x1]
    x2 = res.index("Stop_2")
    bin2 = res[x1+1:x2]
    x3 = res.index("Stop_3")
    bin3 = res[x2+1:x3]

    

    return mezz, pallet,bin1,bin2,bin3,res

def pallet_allocate(request,pallet,pp_id,pp_name):
    bin1 = list(pallet['bins'])
    for i in pp_name:
        for t in bin1:
            OrderManagement.objects.filter(pickbin1=t,orderedqty__gt=0).update(allocated_user1=i)

    for i in pp_name:
        for t in bin1:
            OrderManagement.objects.filter(pickbin2=t,orderedqty__gt=0).update(allocated_user1=i)

    for i in pp_name:
        for t in bin1:
            OrderManagement.objects.filter(pickbin3=t,orderedqty__gt=0).update(allocated_user1=i)




def sequence_structure(request,mezz,p_name):
    a = list(mezz['sequence'])
    a.sort()
    a = pd.DataFrame(a,columns={"Sequence"})
    total = a['Sequence'].sum()
    a['Per'] = round(a['Sequence']/total*100).astype(int)
    a['Cata'] = round(a['Per']/a["Per"].iloc[-1],2)
    pic = len(p_name)
    lis = []
    x = 1
    while x < pic:
        lis.append(x/pic)
        x=x+1
    lis.append(1.01)


    pack = []
    
    for i in lis:
        y = a[a['Cata']<i]
        pack.append(list(y['Sequence']))
        a = a[~a['Sequence'].isin(y['Sequence'])]


    pack = pd.DataFrame(pack)
    pack = pack.transpose()

    pack.columns = p_name

    pack = pack.fillna(0)
    pack = pack.astype('int')

    return pack

def user_allocate(request,pack,bin1,bin2,bin3,p_name,mezz):
    
    for i in bin1:
        print(i)
        for t in p_name:
            print(t)
            for x in pack[t]:
                if x == 0:
                    pass
                else:
                    if i == mezz[mezz['sequence']==x]['bins'].values[0]:
                        print(t)
                        OrderManagement.objects.filter(pickbin1=i,orderedqty__gt=0).update(allocated_user1=t)
                    else:
                        pass

    for i in bin2:
        print(i)
        for t in p_name:
            print(t)
            for x in pack[t]:
                if x == 0:
                    pass
                else:
                    if i == mezz[mezz['sequence']==x]['bins'].values[0]:
                        print(t)
                        OrderManagement.objects.filter(pickbin2=i,orderedqty__gt=0).update(allocated_user2=t)
                    else:
                        pass

    for i in bin3:
        print(i)
        for t in p_name:
            print(t)
            for x in pack[t]:
                if x == 0:
                    pass
                else:
                    if i == mezz[mezz['sequence']==x]['bins'].values[0]:
                        print(t)
                        OrderManagement.objects.filter(pickbin3=i,orderedqty__gt=0).update(allocated_user3=t)
                    else:
                        pass
            #OrderManagement.objects.filter(pickbin1=i,orderedqty__gt=0).update()
    

def bin_selection(request,productcode, qty):
    bins = list(BinContent.objects.filter(productcode=productcode).values_list("bin","avail_qty"))

    #Transfer list
    bin_picks = []
    pickqty = []

    #Processing list
    b = []
    c = []

    for i in bins:
        b.append(i[0])
        c.append(i[1])
    d = {'Bin':b,'qty':c}
    df = pd.DataFrame(d)

    while qty > 0:
        def closest(c, qty):
            return c[min(range(len(c)), key = lambda i: abs(c[i]-qty))]
        clos = closest(c, qty)
 

        bin_picks.append(b[c.index(clos)])

        if clos < qty:
            pickqty.append(clos)
        else:
            pickqty.append(qty)

        b.remove(b[c.index(clos)])
        c.remove(clos)
        qty = qty - clos

    
        if qty < 0 or qty == 0 or len(c) == 0:
            break
        else:
            continue

    return bin_picks, pickqty
    
def update_allocate(request):
    verify = OrderManagement.objects.filter(status1=linestatus[7]).first()

    #Back Orders
    if verify is None:
        pass
    else:
        BO =OrderManagement.objects.all().filter(status1=linestatus[7])
        x = len(BO)
        y = 0
        while x > 0:
            productcode =BO[y].productcode
            orderno = BO[y].orderno
            OrderLines.objects.filter(orderno=orderno, productcode=productcode).update(linestatus=linestatus[7])
            OrderManagement.clear_positions(productcode,orderno)
            y = y + 1
            x = x - 1


    verify =  OrderManagement.objects.filter(status1=linestatus[4]).first()

    if verify is None:
        pass
    else:
        PC = OrderManagement.objects.all().filter(status1=linestatus[4])
        x = len(PC)
        y = 0
        while x > 0:
            productcode = PC[0].productcode
            orderno = PC[0].orderno
            OrderManagement.clear_positions(productcode,orderno)
            y = y + 1
            x = x - 1

    unallocationlist = list(OrderManagement.objects.filter(allocated=True).values_list('station', flat=True).distinct().order_by("id"))
    unique_station = []
    for i in unallocationlist:
        if i not in unique_station:
            unique_station.append(i)
    
    for i in unique_station:
        pos = int(OrderManagement.objects.filter(station=i,orderedqty__gt=0).count())
        alloc = int(OrderManagement.objects.filter(station=i,allocated=True).count())
        
        if pos == 0 and alloc > 0:
            OrderManagement.objects.filter(station=i).update(allocated=False)
        else:
            pass

def load_order(request,orderlist, unique_station):
    x = len(unique_station)
    y = 0
    a = len(orderlist)
    while y < a:
        next_all = OrderLines.objects.filter(orderno=orderlist[y])
        s = 1
        for c in next_all:
            verify = BinContent.objects.filter(productcode=c.productcode).first()
            if verify is None:
                qty = 0
                status = linestatus[7]
                bin_picks=["NA",'NA','NA']
                pickqty=[0,0,0]
            else:
                qty = OrderLines.objects.filter(productcode=c.productcode,orderno=orderlist[y]).values('productcode').annotate(total = Sum('qtyordered'))
                av_qty = BinContent.objects.filter(productcode=c.productcode).values('productcode').annotate(total = Sum('qty'))
                av_qty = int(av_qty[0].get('total'))
                qty = int(qty[0].get("total"))
                status = linestatus[0]
                productcode = c.productcode
                bin_picks,pickqty = bin_selection(request,productcode,qty)
                o = 0
                if len(bin_picks) == 1:
                    bin_picks.append("NA")
                    bin_picks.append("NA")
                    pickqty.append(o)
                    pickqty.append(o)
                elif len(bin_picks)==2:
                    bin_picks.append("NA")
                    pickqty.append(o)
                else:
                    pass
            
            OrderManagement.objects.filter(station=unique_station[y],position=s).update(orderno =orderlist[y], 
                                                                                        productcode=c.productcode, 
                                                                                        orderedqty=c.qtyordered,
                                                                                        availableqty=av_qty,
                                                                                        status1=status,
                                                                                        status2=status,
                                                                                        status3=status,
                                                                                        pickbin1=bin_picks[0],
                                                                                        pickbin2 = bin_picks[1],
                                                                                        pickbin3=bin_picks[2],
                                                                                        pickqty1=pickqty[0],
                                                                                        pickqty2=pickqty[1],
                                                                                        pickqty3=pickqty[2])

            qty_left = c.qtyordered - pickqty[0] -pickqty[1]-pickqty[2]
            OrderManagement.objects.filter(station=unique_station[y]).update(allocated=True)
            OrderManagement.objects.filter(orderno =orderlist[y],productcode=c.productcode,).update(unallocatedqty=qty_left)
            Orders.objects.filter(orderno=orderlist[y]).update(orderstatus=orderstatus[1])

            s = s + 1
        y = y + 1
        if y < x:
            continue
        else:
            break



def ordermanagement(request):
    user_d = request.user
    data = OrderManagement.objects.all().filter(orderedqty__gt=0)
    if "schedule" in request.POST:

        update_allocate(request)

        verify = Orders.objects.filter(orderstatus=orderstatus[0]).first()
        if verify is None:
            messages.warning(request,"The is not available Orders to allocate")
            return render(request,"links_app/systemcontrol/systemmaintenance/ordermanagement.html",{"user_d":user_d,"data":data})
        else:
            verify = OrderManagement.objects.filter(allocated=False).first()
            if verify is None:
                messages.warning(request,"Allocation capacity maxed, please waiting a few mintues")
                return render(request,"links_app/systemcontrol/systemmaintenance/ordermanagement.html",{"user_d":user_d,"data":data})
            else:
                orderlist = list(Orders.objects.filter(orderstatus=orderstatus[0]).values_list('orderno', flat=True).distinct().order_by("id"))
                allocationlist = list(OrderManagement.objects.filter(allocated=False).values_list('station', flat=True).distinct().order_by("id"))
                
                unique_station = []
                for i in allocationlist:
                    if i not in unique_station:
                        unique_station.append(i)
                
                load_order(request,orderlist, unique_station)

                p_id,p_name,pp_id,pp_name = get_pickers(request)
                mezz, pallet,bin1,bin2,bin3,res = get_bins(request)
                pallet_allocate(request,pallet,pp_id,pp_name)
                if len(res) == 3:
                    return render(request,"links_app/systemcontrol/systemmaintenance/ordermanagement.html",{"user_d":user_d,"data":data})
                else:
                    pack = sequence_structure(request,mezz,p_name)
                    user_allocate(request,pack,bin1,bin2,bin3,p_name,mezz)


                return render(request,"links_app/systemcontrol/systemmaintenance/ordermanagement.html",{"user_d":user_d,"data":data})


    return render(request,"links_app/systemcontrol/systemmaintenance/ordermanagement.html",{"user_d":user_d,"data":data})

def allocationcapacity(request):
    user_d = request.user
    if "upload_pm" in request.POST:
        col_no = 3
        df = uploader(request, col_no)
        for i in df.iterrows():
            AllocateCapacity.objects.filter(station = i[1][0]).delete()
            el = AllocateCapacity.objects.create(station=i[1][0])
            el.active = i[1][1]
            el.station_type = i[1][2]
            el.save()

        messages.warning(request, "allocated Capacity successfully updated")

    form = CsvImportForm()
    data = {'form':form,"user_d":user_d}
    return render(request,"links_app/systemcontrol/systemmaintenance/allocationcapacity.html",data)



def orderschedule(request):
    user_d = request.user
    df = no_of_picks(request)
    if "schedule" in request.POST:
        allocated_orders = orderSlot(request)
        newOrderRequest(request,allocated_orders)
        p_id,p_name,pp_id,pp_name=get_pickers(request)
        user_slot(request,p_id,p_name,pp_id,pp_name)
    elif "distribute" in request.POST and "select" in request.POST:
        select = request.POST['select']
        distribute_picks(request,select)
    else:
        pass
    return render(request,"links_app/systemcontrol/systemmaintenance/orderschedule.html",{"user_d":user_d,"df":df})


def orderSlot(request):
    orderList = list(Orders.objects.filter(orderstatus="New").values_list('orderno', flat=True).distinct().order_by("id"))

    unique_orders = []
    for i in orderList:
        if i not in unique_orders:
            unique_orders.append(i)
    
    station_list = list(AllocateCapacity.objects.filter(orderno="", active='TRUE',station_type="Normal").values_list("station",flat=True).distinct().order_by("id"))
    x = len(station_list)
    y = len(unique_orders)

    allocated_orders = []
    a = 0
    while x > 0:
        if y == 0:
            break
        else:
            AllocateCapacity.objects.filter(station=station_list[0]).update(orderno=unique_orders[0])
            allocated_orders.append(unique_orders[0])
            station_list.remove(station_list[0])
            unique_orders.remove(unique_orders[0])
            x = x - 1
            y = y - 1

    return allocated_orders


def newOrderRequest(request,allocated_orders):
    #list view of new orders
    #orderList = list(Orders.objects.filter(orderstatus="New").values_list('orderno', flat=True).distinct().order_by("id"))
    for order in allocated_orders:
        #get list of productcode within orderno as well as qty ordered
        item = list(OrderLines.objects.filter(orderno=order).values_list('productcode', "qtyordered"))
        itemList = []
        qtyList = []

        for i in item:
            itemList.append(i[0])
            qtyList.append(i[1])

        x = 0
        for t in itemList:
            verify = BinContent.objects.filter(productcode=t).first()
            if verify is None:
                #back order Updated
                OrderLines.objects.filter(orderno=order,productcode=t).update(linestatus='BackOrder')
            else:
                av_qty = BinContent.objects.filter(productcode=t).values('productcode').annotate(total = Sum('qty'))
                av_qty = int(av_qty[0].get('total'))
            
                productcode = t
                qty = qtyList[x]

                un_qty = av_qty - qty
                if un_qty > 0:
                    un_qty = 0
                else:
                    un_qty = un_qty*-1

                x = x + 1

                bin_picks, pickqty = bin_selection(request,productcode, qty)

                print(bin_picks)
                print(pickqty)

                y = 0
                for f  in bin_picks:
                    sel_bin = f
                    sel_qty = pickqty[y]
                    OrderSchedule.loadNewLine(order,sel_bin, sel_qty,productcode,qty,av_qty,un_qty)
                    y = y +1
        Orders.objects.filter(orderno=order).update(orderstatus="Allocated")


def user_slot(request,p_id,p_name,pp_id,pp_name):
    binList = list(OrderSchedule.objects.filter(status="Allocated",allocated_user="").values_list('allocated_bin', flat=True).distinct().order_by("id"))
    
    seqs = []
    area = []
    for binn in binList:
        a = BinContent.objects.get(bin=binn).picksequenece
        b = BinContent.objects.get(bin=binn).area

        seqs.append(a)
        area.append(b)

    df = {"area":area,"bins":binList,"sequence":seqs}
    df = pd.DataFrame(df, columns={"area","bins",'sequence'})

    place = list(df['area'].unique())


    for area_r in place:
        seq = list(df[df['area']==area_r]['sequence'])

        if area_r == "Pallet":
            p = pp_name
        else:
            p = p_name

        seq.sort()


        t = round(len(seq)/len(p),0)
        if t == 0 or t== 0.0:
            t = 1
        else:
            pass

        for i in p:
            x = 0
            while x < t:
                if seq == []:
                    break
                else:
                    print(seq[0])
                    binnn = BinContent.objects.get(area=area_r,picksequenece=seq[0]).bin
                    OrderSchedule.objects.filter(allocated_bin=binnn).update(allocated_user=i)
                    seq.remove(seq[0])
                    x = x +1

        if seq == []:
            pass
        else:
            for i in seq:
                binnn = BinContent.objects.get(area=area_r,picksequenece=i).bin
                OrderSchedule.objects.filter(allocated_bin=binnn).update(allocated_user=p[-1])


def no_of_picks(request):
    pickers = []
    bin = []

    verify = OrderSchedule.objects.filter().first()
    if verify is None:
        df = []
    else:
        data = OrderSchedule.objects.all()
        for i in data:
            pickers.append(i.allocated_user)
            #a = BinContent.objects.get(i.allocated_bin).area
            bin.append(i.allocated_bin)

        df = {"pickers":pickers,"bin":bin}
        dff = pd.DataFrame(df,columns={"pickers","bin"})

        dff['Area'] = "Mezz"+dff['bin'].str[:1]

        dff = pd.pivot_table(dff, index=['pickers'], columns='Area', values='Area', aggfunc='count').rename_axis(index=None, columns=None)


        dff.reset_index(inplace=True)
        dff.fillna(0, inplace=True)
        col = list(dff.columns)

        dff['Sum'] = dff[col].sum(numeric_only=True,axis=1)
        

        count = len(col)

        dff.iloc[:, 1:count] = dff.iloc[:, 1:count].astype(int)

        dff['Sum'] = dff['Sum'].astype(int)

        pickers = list(dff['index'].unique())

        picks = []
        for i in pickers:
            a = OrderSchedule.objects.filter(Q(status="Picked")|Q(status="PickStaging"),allocated_user=i).count()
            picks.append(a)
        

        dff['Picks'] = picks
        
        dff['Per'] = round(dff['Picks']/dff['Sum']*100,0)

        df = dff.to_dict('records')
    return df


def distribute_picks(request,select):

    if select == "":
        pass
    else:
        verify = OrderSchedule.objects.filter(allocated_user=select,status="Allocated").first()
        if verify is None:
            pass
        else:
            data = OrderSchedule.objects.all().filter(allocated_user=select,status="Allocated")


            order = []
            product = []
            binn = []

            for i in data:
                order.append(i.orderno)
                product.append(i.productcode)
                binn.append(i.allocated_bin)


            df = {"order":order,"binn":binn,"productcode":product}
            dff = pd.DataFrame(df,columns= {'order',"binn","productcode"})

            dff['id'] = dff['order'] + dff['binn']

            idlist = list(dff['id'])

            avail_users = list(OrderSchedule.objects.filter(Q(status="Allocated")|Q(status="Picked")).values_list('allocated_user', flat=True))

            all_users = []
            for i in avail_users:
                if i not in all_users:
                    all_users.append(i)

            all_users.remove(select)

            t = round(len(data)/len(all_users),0)
            if t == 0 or t== 0.0:
                t = 1
            else:
                pass

            for i in all_users:
                x = 0
                while x < t:
                    if idlist == []:
                        break
                    else:
                        idlist[0]
                        o = dff[dff['id']==idlist[0]]['order'].values[0]
                        pc = dff[dff['id']==idlist[0]]['productcode'].values[0]
                        b = dff[dff['id']==idlist[0]]['binn'].values[0]
                        OrderSchedule.objects.filter(orderno=o,productcode=pc,allocated_bin=b).update(allocated_user=i)
                        idlist.remove(idlist[0])
                        print(idlist)

                        x =x +1

            if idlist == []:
                pass
            else:
                for i in idlist:
                    o = dff[dff['id']==i]['order'].values[0]
                    pc = dff[dff['id']==i]['productcode'].values[0]
                    b = dff[dff['id']==i]['binn'].values[0]
                    OrderSchedule.objects.filter(orderno=o,productcode=pc,allocated_bin=b).update(allocated_user=all_users[-1])

      
def user_picks(request):
    user_d = request.user
    verify = OrderSchedule.objects.filter(allocated_user=str(user_d),status="Allocated").first()
    if verify is None:
        data = {"orderno":0,"productcode":0,"allocated_bin_qty":0}
    else:
        data = OrderSchedule.objects.all().filter(allocated_user=str(user_d),status="Allocated")
        data = data[0]

    r = ['submit','hu','productcode','bin','qty',"type"]

    if r[0] in request.POST  and r[1] in request.POST and r[2] in request.POST and r[3] in request.POST and r[4]  in request.POST and r[5] in request.POST:
        req_type = request.POST[r[5]]

        if req_type == "nostock":
            pass
        elif req_type == "wrongstock":
            pass
        elif req_type == "good":
            hu = request.POST[r[1]]
            hu = verify_hu(request,hu)
            if hu == "used":
                messages.warning(request, "HU either in currently in use and cannot be re-used")
            elif hu == "Invalid":
                messages.warning(request, "HU enter is not valid")
            else:
                productcode = request.POST[r[2]]
                verify = verify_PM(request,productcode)
                if verify is None:
                    messages.warning(request, "Productcode doesn't exist")
                else:
                    binn = request.POST[r[3]]
                    t = request.POST[r[0]]
                    qty = int(request.POST[r[4]])

                    order = t.partition('|')[0]
                    t = t.partition('|')[2]
                    req_qty = int(t.partition('_')[0])
                    req_bin = t.partition('_')[2]

                    if binn != req_bin:
                        messages.warning(request, "Incorrect targetbin")
                    else:
                        if req_qty < qty:
                            messages.warning(request, "You picking more than the required qty")
                        else:
                            OrderSchedule.newPickUpdate(order,hu,binn,productcode,qty,user_d)

                            status = OrderLines.objects.get(orderno=order,productcode=productcode).linestatus
                            if status == "Picking":
                                pass
                            else:
                                OrderLines.objects.filter(orderno=order,productcode=productcode).update(linestatus="Picking")
                            
                            status = Orders.objects.get(orderno=order).orderstatus
                            if status == "Picking":
                                pass
                            else:
                                Orders.objects.filter(orderno=order).update(orderstatus="Picking")

                            dept_w = "Outbound"
                            w_type = "Picking"
                            origin=order
                            sourcearea = BinContent.objects.get(bin=binn).area
                            sourcebin = binn
                            initialsoh = int(BinContent.objects.get(bin=binn).qty)
                            resultsoh = initialsoh -qty
                            targetbin = "Interrim"
                            targetarea = "INTRANS"
                            holdingu = hu
                            Transactions.transactions(dept_w,w_type,origin,productcode,sourcearea,sourcebin,initialsoh,qty,resultsoh,targetbin,targetarea,holdingu,user_d)

                            if resultsoh == 0:
                                BinContent.objects.filter(bin=binn).update(productcode="",qty=resultsoh,full="TRUE")
                            else:
                                BinContent.objects.filter(bin=binn).update(qty=resultsoh,full="TRUE")

                            area = "INTRANS"
                            binn = "Interrim"
                            parent = order
                            Interrim.interrims(area,binn,parent,hu,productcode,qty)


                            verify = OrderSchedule.objects.filter(orderno=order,status="Allocated").first()
                            if verify is None:
                                Orders.objects.filter(orderno=order).update(orderstatus="PickStaging")
                                AllocateCapacity.objects.filter(orderno=order).update(orderno="")
                            else:
                                pass

                            verify = OrderSchedule.objects.filter(allocated_user=str(user_d),status="Allocated").first()
                            if verify is None:
                                data = {"orderno":0,"productcode":0,"allocated_bin_qty":0}
                            else:
                                data = OrderSchedule.objects.all().filter(allocated_user=str(user_d),status="Allocated")
                                data = data[0]


                            messages.warning(request, "Item picked successfully")
                            return render(request,"links_app/outbound/user_picks.html",{"user_d":user_d,"data":data})

    return render(request,"links_app/outbound/user_picks.html",{"user_d":user_d,"data":data})


def verify_hu(request,hu):
    token = hu[:3]
    if token == "HUP" and len(hu) == 8:
        verify = Transactions.objects.filter(holdingunit=hu).first()
        if verify is None:
            pass
        else:
            hu = "used"
    elif hu[:2] == "TU" and len(hu) ==6:
        verify = Interrim.objects.filter(holdingunit=hu).first()
        if verify is None:
            verify = AfterPickStaging.objects.filter(Q(holdingunit1=hu)|Q(holdingunit2=hu)|Q(holdingunit3=hu)).first()
            if verify is None:
                pass
            else:
                hu = "used"
        else:
            hu = "used"
    else:
        hu = "Invalid"
    return hu



def outboundStaging(request):
    user_d = request.user
    if "upload_pm" in request.POST:
        col_no = 5
        df = uploader(request, col_no)
        for i in df.iterrows():
            AfterPickStaging.objects.filter(bin = i[1][2]).delete()
            el = AfterPickStaging.objects.create(bin=i[1][2])
            el.hutype = i[1][0]
            el.area = i[1][1]
            el.status = i[1][3]
            el.sequence = i[1][4]
            el.save()

        messages.warning(request, "Pick Staging updated")

    form = CsvImportForm()
    data = {'form':form}
    return render(request, "links_app/systemcontrol/systemmaintenance/outboundstaging.html",data)


def pickStaging(request):
    user_d = request.user
    user_id = User.objects.get(username=str(user_d)).id
    pickertype = Employee.objects.get(user_id=user_id).area
    if "route" in request.POST and "hu" in request.POST:
        hu = request.POST['hu']
        hutype = hu[:2]
        #loadHUP(request,hu,pickertype)
        verify = Interrim.objects.filter(holdingunit=hu).first()
        if verify is None:
            messages.warning(request,"HUP not available for routing")
        else:
            verify = OrderSchedule.objects.filter(status="Picked",pick_hu=hu).first()
            if verify is None:
                messages.warning(request, "HU is not available for Pick Staging")
            else:
                orderno = OrderSchedule.objects.get(status="Picked",pick_hu=hu).orderno
                result = loadHUP(request,hu,pickertype,hutype,orderno)
                if result == "FALSE":
                    messages.warning(request,"Staging currently full, please wait")
                else:
                    messages.warning(request,"HU Staged successfully")

    return render(request, "links_app/outbound/pickstaging.html",{"user_d":user_d})


def loadHUP(request,hu,pickertype,hutype,orderno):
    
    verify = AfterPickStaging.objects.filter(hutype=hutype,status="TRUE",holdingvalue__lt=3).first()
    if verify is None:
        result = "FALSE"
    else:
        verify = AfterPickStaging.objects.filter(Q(holdingvalue=1)|Q(holdingvalue=2),orderno = orderno,hutype=hutype).first()
        if verify is None:
            all = AfterPickStaging.objects.filter(hutype=hutype,holdingvalue=0,status="TRUE").values_list('area','bin',"holdingvalue","sequence")
            
            area = []
            bin = []
            slot = []
            sequence = []

            for i in all:
                area.append(i[0])
                bin.append(i[1])
                slot.append(i[2])
                sequence.append(i[3])

            df = {"area":area,"bin":bin,"slot":slot,"sequence":sequence}
            
            
            all = pd.DataFrame(df,columns= {'area',"bin","slots","sequence"})
            seq = list(all['sequence'])
            seq.sort()
            sel_seq = seq[0]
            binn = all[all["sequence"]==sel_seq]['bin'].values
            print(binn)
            AfterPickStaging.objects.filter(bin=binn[0]).update(holdingunit1=hu,holdingvalue=1,orderno=orderno)
            OrderSchedule.objects.filter(pick_hu=hu).update(status="PickStaging")
            Interrim.objects.filter(holdingunit=hu).delete()

            result = "TRUE"

        else:
            binn = AfterPickStaging.objects.filter(Q(holdingvalue=1)|Q(holdingvalue=2),orderno = orderno).values_list("bin")
            sel_bin = []
            for i in binn:
                sel_bin.append(i[0])

            
            qty = int(AfterPickStaging.objects.get(bin=sel_bin[0]).holdingvalue)

            qty = qty+1


            holder1 = AfterPickStaging.objects.get(bin=sel_bin[0]).holdingunit1
            holder2 = AfterPickStaging.objects.get(bin=sel_bin[0]).holdingunit2


            if holder1 =="" or holder1 ==" ":
                AfterPickStaging.objects.filter(bin=sel_bin[0]).update(holdingunit1=hu,holdingvalue=qty)
                OrderSchedule.objects.filter(pick_hu=hu).update(status="PickStaging")
                Interrim.objects.filter(holdingunit=hu).delete()
            elif holder2 == "" or holder2 == " ":
                AfterPickStaging.objects.filter(bin=sel_bin[0]).update(holdingunit2=hu,holdingvalue=qty)
                OrderSchedule.objects.filter(pick_hu=hu).update(status="PickStaging")
                Interrim.objects.filter(holdingunit=hu).delete()
            else:
                AfterPickStaging.objects.filter(bin=sel_bin[0]).update(holdingunit3=hu,holdingvalue=qty)
                OrderSchedule.objects.filter(pick_hu=hu).update(status="PickStaging")
                Interrim.objects.filter(holdingunit=hu).delete()

            result = "TRUE"

    return result




        


        


   








