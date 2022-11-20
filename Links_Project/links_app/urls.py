from django.urls import path, include
from links_app import views
#from django.conf import settings
#import debug_toolbar

urlpatterns = [
        path("index/",views.index,name='index'),
        path("user_login/",views.user_login, name='user_login'),
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
        path("transactions/",views.transactions, name='transactions'),
        path("create_pickingslip/",views.create_pickingslip,name="create_pickingslip"),
        path("analytics/",views.analytics, name="analytics"),
        path("product_inquire/",views.product_inquire,name='product_inquire'),
]


"""if settings.DEBUG:
    urlpatterns = [
        path("__debug__/",include(debug_toolbar.urls))
    ] + urlpatterns"""



