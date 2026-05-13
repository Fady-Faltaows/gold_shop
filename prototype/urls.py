from django.urls import path
from . import views

urlpatterns = [
    # auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('access-denied/', views.access_denied, name='access_denied'),

    # dashboard
    path('', views.dashboard, name='dashboard'),

    # products
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),

    # categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),

    # inventory
    path('inventory/', views.inventory_list, name='inventory_list'),

    # sales
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/new/', views.sale_create, name='sale_create'),

    # purchases
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/new/', views.purchase_create, name='purchase_create'),

    # reports
    path('reports/', views.reports_home, name='reports_home'),
    path('reports/sales/', views.report_sales, name='report_sales'),
    path('reports/inventory/', views.report_inventory, name='report_inventory'),
    path('reports/profit/', views.report_profit, name='report_profit'),
    path('reports/gold-price/', views.report_gold_price, name='report_gold_price'),
]