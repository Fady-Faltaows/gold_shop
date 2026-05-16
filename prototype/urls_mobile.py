from django.urls import path
from . import views_mobile

app_name = 'mobile'

urlpatterns = [
    path('',           views_mobile.mobile_dashboard,  name='dashboard'),
    path('inventory/', views_mobile.mobile_inventory,  name='inventory'),
    path('sales/',     views_mobile.mobile_sales,      name='sales'),
    path('gold/',      views_mobile.mobile_gold_price, name='gold_price'),
    path('reports/',   views_mobile.mobile_reports,    name='reports'),
]