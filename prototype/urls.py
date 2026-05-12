from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/new/', views.sale_create, name='sale_create'),
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/new/', views.purchase_create, name='purchase_create'),
    path('reports/', views.reports_home, name='reports_home'),
    path('reports/sales/', views.report_sales, name='report_sales'),
    path('reports/inventory/', views.report_inventory, name='report_inventory'),
    path('reports/profit/', views.report_profit, name='report_profit'),
    path('reports/gold-price/', views.report_gold_price, name='report_gold_price'),
    path('products/create/', views.product_create, name='product_create'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/', views.category_list, name='category_list'),
]