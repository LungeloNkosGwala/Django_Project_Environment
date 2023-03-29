from django.urls import path, include
from links_app import views
#from django.conf import settings
#import debug_toolbar

urlpatterns = [
        path("index/",views.index,name='index'),
        path("scanner_index/",views.scanner_index,name="scanner_index"),
        path("user_login/",views.user_login, name='user_login'),
        path("scanner_login/",views.scanner_login,name="scanner_login"),
        path("loadasn/",views.loadasn, name="loadasn"),
        path("pmupdate/",views.pmupdate, name='pmupdate'),
        path("binupdate/",views.binupdate, name='binupdate'),
        path("register/",views.register, name="register"),
        path("createdelivery/",views.createdelivery, name="createdelivery"),
        path("assignuser/", views.assignuser, name="assignuser"),
        path("receiveasn/",views.receiveasn, name="receiveasn"),
        path("putaway/", views.putaway,name="putaway"),
        path("pfep/",views.pfep, name='pfep'),
        path("asn_inquire/",views.asn_inquire,name="asn_inquire"),
        path("bin_inquire/",views.bin_inquire,name="bin_inquire"),
        path("transactions/",views.transactions, name='transactions'),
        path("create_pickingslip/",views.create_pickingslip,name="create_pickingslip"),
        path("analytics/",views.analytics, name="analytics"),
        path("product_inquire/",views.product_inquire,name='product_inquire'),
        path("base_system",views.base_system,name="base_system" ),
        path("cust_routecode",views.cust_routecode,name='cust_routecode'),
        path("routecode_update/",views.routecode_update,name='routecode_update'),
        path("user_management/",views.user_management, name='user_management'),
        path("allocationcapacity/",views.allocationcapacity,name="allocationcapacity"),
        path("base_orderm/",views.base_orderm,name='base_orderm'),
        path("rep_inbound/",views.rep_inbound, name="rep_inbound"),
        path("rep_inventory/",views.rep_inventory,name="rep_inventory"),
        path("orderschedule/", views.orderschedule,name="orderschedule"),
        path("user_picks/",views.user_picks, name='user_picks'),
        path("outboundstaging/",views.outboundStaging, name="outboundstaging"),
        path("pickstaging/",views.pickStaging, name="pickstaging"),
        path("packing/",views.packing,name="packing"),
]


"""if settings.DEBUG:
    urlpatterns = [
        path("__debug__/",include(debug_toolbar.urls))
    ] + urlpatterns"""



