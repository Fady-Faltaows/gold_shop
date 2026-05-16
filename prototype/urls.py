from django.urls import path, include
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

    # crm
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),

    # suppliers
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),
    path('suppliers/<int:pk>/purchases/', views.supplier_purchase_history, name='supplier_purchase_history'),

    # inventory
    path('inventory/', views.inventory_list, name='inventory_list'),

    # sales
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/new/', views.sale_create, name='sale_create'),
    path('sales/<int:sale_id>/receipt/', views.sale_receipt, name='sale_receipt'),
    path('sales/<int:sale_id>/returns/new/', views.sale_return_create, name='sale_return_create'),

    # purchases
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/new/', views.purchase_create, name='purchase_create'),
    path('purchases/<int:purchase_id>/invoice/', views.purchase_invoice, name='purchase_invoice'),

    # expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/new/', views.expense_create, name='expense_create'),

    # reports
    path('reports/', views.reports_home, name='reports_home'),
    path('reports/sales/', views.report_sales, name='report_sales'),
    path('reports/inventory/', views.report_inventory, name='report_inventory'),
    path('reports/profit/', views.report_profit, name='report_profit'),
    path('reports/financial/', views.financial_report, name='financial_report'),
    path('reports/gold-price/', views.report_gold_price, name='report_gold_price'),
    path('reports/sales/export.csv', views.export_sales_csv, name='export_sales_csv'),
    path('reports/inventory/export.csv', views.export_inventory_csv, name='export_inventory_csv'),
    path('reports/financial/export.csv', views.export_financial_csv, name='export_financial_csv'),
    # ── PWA Mobile Monitor ──
    path('mobile/', include('prototype.urls_mobile')),
]
