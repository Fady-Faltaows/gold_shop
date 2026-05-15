import csv
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.db import models
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from .models import Customer, Expense, GoldPrice, Category, Product, Inventory, Sale, SaleItem, SaleReturn, Purchase, Branch, Supplier
from .forms import (
    CategoryForm,
    CustomerForm,
    ExpenseForm,
    GoldPriceForm,
    ProductForm,
    PurchaseForm,
    SaleForm,
    SaleItemForm,
    SaleReturnForm,
    SupplierForm,
)
from .decorators import admin_required, cashier_or_admin


# ─────────────────────────────────────────────
# AUTH VIEWS
# ─────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user     = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}! 👋')
            return redirect('dashboard')
        else:
            messages.error(request, '❌ Invalid username or password.')

    return render(request, 'prototype/auth/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('login')


def access_denied(request):
    return render(request, 'prototype/auth/access_denied.html')


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────

@cashier_or_admin
def dashboard(request):
    latest_gold    = GoldPrice.objects.order_by('-updated_at').first()
    branch_filter  = get_branch_filter(request)
    total_products = Product.objects.count()
    total_sales    = Sale.objects.filter(**branch_filter).count()
    total_profit   = sum(sale.get_total_profit() for sale in Sale.objects.filter(**branch_filter))
    low_stock      = Inventory.objects.filter(
        **branch_filter,
        quantity_pieces__lte=models.F('product__low_stock_threshold')
    )

    if request.method == 'POST':
        form = GoldPriceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Gold price updated successfully!')
            return redirect('dashboard')
    else:
        form = GoldPriceForm()

    context = {
        'latest_gold':    latest_gold,
        'total_products': total_products,
        'total_sales':    total_sales,
        'total_profit':   total_profit,
        'low_stock':      low_stock,
        'gold_form':      form,
    }
    return render(request, 'prototype/dashboard.html', context)


# ─────────────────────────────────────────────
# PRODUCTS
# ─────────────────────────────────────────────

@admin_required
def product_list(request):
    products = Product.objects.select_related('category', 'preferred_supplier').all()
    return render(request, 'prototype/product_list.html', {'products': products})


@admin_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Product added successfully!')
            return redirect('product_list')
    else:
        form = ProductForm()

    categories = Category.objects.all()
    return render(request, 'prototype/product_create.html', {
        'form':       form,
        'categories': categories,
    })


# ─────────────────────────────────────────────
# CATEGORIES
# ─────────────────────────────────────────────

@admin_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'prototype/category_list.html', {'categories': categories})


@admin_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Category added successfully!')
            next_url = request.POST.get('next', 'category_list')
            return redirect(next_url)
    else:
        form = CategoryForm()

    return render(request, 'prototype/category_create.html', {'form': form})


# ─────────────────────────────────────────────
# CRM
# ─────────────────────────────────────────────

@admin_required
def customer_list(request):
    query = request.GET.get('q', '').strip()
    customers = Customer.objects.order_by('full_name')

    if query:
        customers = customers.filter(
            models.Q(full_name__icontains=query) |
            models.Q(customer_code__icontains=query) |
            models.Q(phone__icontains=query) |
            models.Q(email__icontains=query)
        )

    return render(request, 'prototype/customer_list.html', {
        'customers': customers,
        'query': query,
    })


@admin_required
def customer_create(request):
    next_url = request.GET.get('next') or request.POST.get('next') or 'customer_list'

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer {customer.full_name} added successfully!')
            return redirect(next_url)
    else:
        form = CustomerForm()

    return render(request, 'prototype/customer_create.html', {
        'form': form,
        'next_url': next_url,
    })


@admin_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        name = customer.full_name
        customer.delete()
        messages.success(request, f'Customer {name} removed successfully.')
        return redirect('customer_list')

    return render(request, 'prototype/confirm_delete.html', {
        'object_name': customer.full_name,
        'cancel_url': 'customer_list',
        'title': 'Remove Customer',
    })


# ─────────────────────────────────────────────
# SUPPLIERS
# ─────────────────────────────────────────────

@admin_required
def supplier_list(request):
    query = request.GET.get('q', '').strip()
    suppliers = Supplier.objects.order_by('name')

    if query:
        suppliers = suppliers.filter(
            models.Q(name__icontains=query) |
            models.Q(supplier_code__icontains=query) |
            models.Q(contact_person__icontains=query) |
            models.Q(phone__icontains=query) |
            models.Q(email__icontains=query)
        )

    return render(request, 'prototype/supplier_list.html', {
        'suppliers': suppliers,
        'query': query,
    })


@admin_required
def supplier_create(request):
    next_url = request.GET.get('next') or request.POST.get('next') or 'supplier_list'

    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Supplier {supplier.name} added successfully!')
            return redirect(next_url)
    else:
        form = SupplierForm()

    return render(request, 'prototype/supplier_create.html', {
        'form': form,
        'next_url': next_url,
    })


@admin_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == 'POST':
        name = supplier.name
        supplier.delete()
        messages.success(request, f'Supplier {name} removed successfully.')
        return redirect('supplier_list')

    return render(request, 'prototype/confirm_delete.html', {
        'object_name': supplier.name,
        'cancel_url': 'supplier_list',
        'title': 'Remove Supplier',
    })


@admin_required
def supplier_purchase_history(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    purchases = Purchase.objects.filter(supplier=supplier).select_related('product', 'branch').order_by('-created_at')
    total_cost = sum(purchase.get_total_cost() for purchase in purchases)

    return render(request, 'prototype/supplier_purchase_history.html', {
        'supplier': supplier,
        'purchases': purchases,
        'total_cost': total_cost,
    })


# ─────────────────────────────────────────────
# INVENTORY
# ─────────────────────────────────────────────

@admin_required
def inventory_list(request):
    branch_id = request.GET.get('branch')
    inventory = Inventory.objects.select_related('product', 'branch').all()

    if branch_id:
        inventory = inventory.filter(branch_id=branch_id)

    branches = Branch.objects.filter(is_active=True)

    return render(request, 'prototype/inventory_list.html', {
        'inventory': inventory,
        'branches':  branches,
        'selected_branch': branch_id,
    })


# ─────────────────────────────────────────────
# SALES
# ─────────────────────────────────────────────

@cashier_or_admin
def sale_list(request):
    branch_id = request.GET.get('branch')

    if request.user.profile.is_admin():
        sales    = Sale.objects.select_related('customer', 'branch').order_by('-created_at')
        branches = Branch.objects.filter(is_active=True)
        if branch_id:
            sales = sales.filter(branch_id=branch_id)
    else:
        sales    = Sale.objects.select_related('customer', 'branch').filter(
            branch=request.user.profile.branch
        ).order_by('-created_at')
        branches = None

    return render(request, 'prototype/sale_list.html', {
        'sales':           sales,
        'branches':        branches,
        'selected_branch': branch_id,
    })

@cashier_or_admin
def sale_create(request):
    latest_gold = GoldPrice.objects.order_by('-updated_at').first()
    branches    = Branch.objects.filter(is_active=True)

    # تحديد الفرع
    if request.user.profile.is_admin():
        branch_id     = request.GET.get('branch') or request.POST.get('branch')
        selected_branch = Branch.objects.filter(id=branch_id).first() if branch_id else None
    else:
        selected_branch = request.user.profile.branch

    # فلتر المنتجات حسب الفرع المختار
    if selected_branch:
        branch_products = Inventory.objects.filter(
            branch=selected_branch,
            quantity_pieces__gt=0
        ).values_list('product_id', flat=True)

        products = Product.objects.filter(
            id__in=branch_products
        ).select_related('category')

        inventory_map = {
            inv.product_id: inv.quantity_pieces
            for inv in Inventory.objects.filter(branch=selected_branch)
        }
    else:
        products      = Product.objects.none()
        inventory_map = {}

    if request.method == 'POST':
        sale_form = SaleForm(request.POST)
        if sale_form.is_valid():

            if not selected_branch:
                messages.error(request, '⚠️ Please select a branch first!')
                return redirect('sale_create')

            sale = sale_form.save(commit=False)
            if sale.customer and not sale.customer_name:
                sale.customer_name = sale.customer.full_name

            if latest_gold:
                sale.gold_price_at_sale = latest_gold.price_per_gram
            else:
                messages.error(request, '⚠️ Cannot create sale — no gold price set!')
                return redirect('sale_create')

            sale.branch = selected_branch
            sale.save()

            product_ids = request.POST.getlist('product')
            quantities  = request.POST.getlist('quantity')
            has_error   = False

            for product_id, quantity in zip(product_ids, quantities):
                if product_id and quantity:
                    try:
                        product = Product.objects.get(id=product_id)
                        qty     = int(quantity)

                        if qty <= 0:
                            continue

                        inventory = Inventory.objects.get(
                            product=product,
                            branch=selected_branch
                        )

                        if inventory.quantity_pieces < qty:
                            messages.error(
                                request,
                                f'⚠️ Not enough stock for {product.name}. '
                                f'Available: {inventory.quantity_pieces}'
                            )
                            has_error = True
                            break

                        SaleItem.objects.create(
                            sale=sale,
                            product=product,
                            quantity=qty,
                            price_per_piece=0,
                            cost_per_piece=0,
                        )

                        inventory.quantity_pieces -= qty
                        inventory.save()

                    except (Product.DoesNotExist, Inventory.DoesNotExist):
                        messages.error(request, '⚠️ Product not available in this branch.')
                        has_error = True
                        break

            if has_error:
                sale.delete()
                return redirect('sale_create')

            messages.success(request, f'✅ Sale #{sale.id} created successfully!')
            return redirect('sale_receipt', sale_id=sale.id)

    else:
        sale_form = SaleForm()

    context = {
        'sale_form':       sale_form,
        'products':        products,
        'latest_gold':     latest_gold,
        'gold_price_js':   float(latest_gold.price_per_gram) if latest_gold else 0,
        'inventory_map':   inventory_map,
        'branches':        branches,
        'selected_branch': selected_branch,
    }
    return render(request, 'prototype/sale_create.html', context)


@cashier_or_admin
def sale_receipt(request, sale_id):
    sale = get_object_or_404(
        Sale.objects.select_related('customer', 'branch').prefetch_related('items__product'),
        id=sale_id,
    )
    return render(request, 'prototype/sale_receipt.html', {'sale': sale})


@admin_required
def sale_return_create(request, sale_id):
    sale = get_object_or_404(Sale.objects.select_related('branch'), id=sale_id)

    if request.method == 'POST':
        form = SaleReturnForm(request.POST)
        form.fields['sale_item'].queryset = sale.items.select_related('product')
        if form.is_valid():
            sale_return = form.save(commit=False)
            if sale_return.quantity > sale_return.sale_item.quantity:
                messages.error(request, 'Return quantity cannot exceed the sold quantity.')
                return redirect('sale_return_create', sale_id=sale.id)

            sale_return.branch = sale.branch
            sale_return.save()

            if sale_return.restock:
                inventory, created = Inventory.objects.get_or_create(
                    product=sale_return.sale_item.product,
                    branch=sale.branch,
                    defaults={'quantity_pieces': 0}
                )
                inventory.quantity_pieces += sale_return.quantity
                inventory.save()

            messages.success(request, 'Return recorded successfully.')
            return redirect('sale_list')
    else:
        form = SaleReturnForm()
        form.fields['sale_item'].queryset = sale.items.select_related('product')

    return render(request, 'prototype/sale_return_create.html', {
        'form': form,
        'sale': sale,
    })

# ─────────────────────────────────────────────
# PURCHASES
# ─────────────────────────────────────────────

@admin_required
def purchase_list(request):
    branch_id = request.GET.get('branch')
    purchases = Purchase.objects.select_related('product', 'branch', 'supplier').order_by('-created_at')

    if branch_id:
        purchases = purchases.filter(branch_id=branch_id)

    branches = Branch.objects.filter(is_active=True)

    return render(request, 'prototype/purchase_list.html', {
        'purchases': purchases,
        'branches':  branches,
        'selected_branch': branch_id,
    })


@admin_required
def purchase_invoice(request, purchase_id):
    purchase = get_object_or_404(
        Purchase.objects.select_related('product', 'branch', 'supplier'),
        id=purchase_id,
    )
    return render(request, 'prototype/purchase_invoice.html', {'purchase': purchase})


@admin_required
def purchase_create(request):
    latest_gold = GoldPrice.objects.order_by('-updated_at').first()
    products    = Product.objects.select_related('category').all()
    branches    = Branch.objects.filter(is_active=True)

    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            purchase    = form.save(commit=False)
            branch_id   = request.POST.get('branch')
            if purchase.supplier and not purchase.supplier_name:
                purchase.supplier_name = purchase.supplier.name

            if not latest_gold:
                messages.error(request, '⚠️ Cannot create purchase — no gold price set!')
                return redirect('purchase_create')

            if not branch_id:
                messages.error(request, '⚠️ Please select a branch!')
                return redirect('purchase_create')

            purchase.branch         = Branch.objects.get(id=branch_id)
            purity                  = purchase.product.get_purity()
            purchase.cost_per_piece = latest_gold.price_per_gram * purity * purchase.product.weight_grams
            purchase.save()

            inventory, created = Inventory.objects.get_or_create(
                product=purchase.product,
                branch=purchase.branch,
                defaults={'quantity_pieces': 0}
            )
            inventory.quantity_pieces += purchase.quantity_purchased
            inventory.save()

            messages.success(
                request,
                f'✅ Added {purchase.quantity_purchased} pieces of '
                f'{purchase.product.name} to {purchase.branch.name}!'
            )
            return redirect('purchase_invoice', purchase_id=purchase.id)
    else:
        form = PurchaseForm()

    return render(request, 'prototype/purchase_create.html', {
        'form':          form,
        'gold_price_js': float(latest_gold.price_per_gram) if latest_gold else 0,
        'products':      products,
        'branches':      branches,
    })


# ─────────────────────────────────────────────
# EXPENSES / FINANCE
# ─────────────────────────────────────────────

@admin_required
def expense_list(request):
    branch_id = request.GET.get('branch')
    expenses = Expense.objects.select_related('branch').order_by('-paid_at')

    if branch_id:
        expenses = expenses.filter(branch_id=branch_id)

    return render(request, 'prototype/expense_list.html', {
        'expenses': expenses,
        'branches': Branch.objects.filter(is_active=True),
        'selected_branch': branch_id,
    })


@admin_required
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense recorded successfully.')
            return redirect('expense_list')
    else:
        form = ExpenseForm()

    return render(request, 'prototype/expense_create.html', {'form': form})


@admin_required
def financial_report(request):
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    branch_id = request.GET.get('branch')
    branches = Branch.objects.filter(is_active=True)

    sales = Sale.objects.select_related('branch').order_by('-created_at')
    purchases = Purchase.objects.select_related('branch').order_by('-created_at')
    expenses = Expense.objects.select_related('branch').order_by('-paid_at')
    returns = SaleReturn.objects.select_related('branch').order_by('-created_at')

    if date_from:
        sales = sales.filter(created_at__date__gte=date_from)
        purchases = purchases.filter(created_at__date__gte=date_from)
        expenses = expenses.filter(paid_at__gte=date_from)
        returns = returns.filter(created_at__date__gte=date_from)
    if date_to:
        sales = sales.filter(created_at__date__lte=date_to)
        purchases = purchases.filter(created_at__date__lte=date_to)
        expenses = expenses.filter(paid_at__lte=date_to)
        returns = returns.filter(created_at__date__lte=date_to)
    if branch_id:
        sales = sales.filter(branch_id=branch_id)
        purchases = purchases.filter(branch_id=branch_id)
        expenses = expenses.filter(branch_id=branch_id)
        returns = returns.filter(branch_id=branch_id)

    total_revenue = sum(sale.get_total() for sale in sales)
    gross_profit = sum(sale.get_total_profit() for sale in sales)
    purchase_outflow = sum(purchase.get_total_cost() for purchase in purchases)
    expense_outflow = sum(expense.amount for expense in expenses)
    refund_outflow = sum(sale_return.refund_amount for sale_return in returns)
    cash_in = total_revenue
    cash_out = purchase_outflow + expense_outflow + refund_outflow

    return render(request, 'prototype/reports/financial.html', {
        'branches': branches,
        'selected_branch': branch_id,
        'date_from': date_from or '',
        'date_to': date_to or '',
        'total_revenue': total_revenue,
        'gross_profit': gross_profit,
        'purchase_outflow': purchase_outflow,
        'expense_outflow': expense_outflow,
        'refund_outflow': refund_outflow,
        'cash_in': cash_in,
        'cash_out': cash_out,
        'net_cash_flow': cash_in - cash_out,
        'net_profit': gross_profit - expense_outflow - refund_outflow,
        'expenses': expenses[:25],
        'returns': returns[:25],
    })


# ─────────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────────
@admin_required
def reports_home(request):
    branches = Branch.objects.filter(is_active=True)
    return render(request, 'prototype/reports/home.html', {'branches': branches})

@admin_required
def report_sales(request):
    date_from  = request.GET.get('date_from')
    date_to    = request.GET.get('date_to')
    branch_id  = request.GET.get('branch')
    branches   = Branch.objects.filter(is_active=True)
    sales      = Sale.objects.order_by('-created_at').select_related('branch')

    if date_from:
        sales = sales.filter(created_at__date__gte=date_from)
    if date_to:
        sales = sales.filter(created_at__date__lte=date_to)
    if branch_id:
        sales = sales.filter(branch_id=branch_id)

    total_revenue = sum(sale.get_total() for sale in sales)
    total_profit  = sum(sale.get_total_profit() for sale in sales)
    total_count   = sales.count()

    # totals per branch
    branch_totals = []
    for branch in branches:
        branch_sales   = sales.filter(branch=branch)
        branch_revenue = sum(s.get_total() for s in branch_sales)
        branch_profit  = sum(s.get_total_profit() for s in branch_sales)
        branch_totals.append({
            'branch':  branch,
            'count':   branch_sales.count(),
            'revenue': branch_revenue,
            'profit':  branch_profit,
        })

    context = {
        'sales':           sales,
        'total_revenue':   total_revenue,
        'total_profit':    total_profit,
        'total_count':     total_count,
        'branches':        branches,
        'branch_totals':   branch_totals,
        'selected_branch': branch_id,
        'date_from':       date_from or '',
        'date_to':         date_to or '',
    }
    return render(request, 'prototype/reports/sales.html', context)

@admin_required
def report_inventory(request):
    branch_id    = request.GET.get('branch')
    branches     = Branch.objects.filter(is_active=True)
    inventory    = Inventory.objects.select_related(
        'product', 'product__category', 'branch'
    ).order_by('branch', 'quantity_pieces')

    if branch_id:
        inventory = inventory.filter(branch_id=branch_id)

    out_of_stock = inventory.filter(quantity_pieces=0)
    low_stock    = inventory.filter(
        quantity_pieces__gt=0,
        quantity_pieces__lte=models.F('product__low_stock_threshold')
    )
    in_stock     = inventory.filter(quantity_pieces__gt=models.F('product__low_stock_threshold'))

    # totals per branch
    branch_totals = []
    for branch in branches:
        branch_inv = inventory.filter(branch=branch)
        branch_totals.append({
            'branch':       branch,
            'total':        branch_inv.count(),
            'out_of_stock': branch_inv.filter(quantity_pieces=0).count(),
            'low_stock':    branch_inv.filter(
                quantity_pieces__gt=0,
                quantity_pieces__lte=models.F('product__low_stock_threshold')
            ).count(),
            'in_stock':     branch_inv.filter(quantity_pieces__gt=models.F('product__low_stock_threshold')).count(),
        })

    context = {
        'inventory':       inventory,
        'out_of_stock':    out_of_stock,
        'low_stock':       low_stock,
        'in_stock':        in_stock,
        'branches':        branches,
        'branch_totals':   branch_totals,
        'selected_branch': branch_id,
    }
    return render(request, 'prototype/reports/inventory.html', context)

@admin_required
def report_profit(request):
    date_from  = request.GET.get('date_from')
    date_to    = request.GET.get('date_to')
    branch_id  = request.GET.get('branch')
    branches   = Branch.objects.filter(is_active=True)
    sales      = Sale.objects.order_by('created_at').select_related('branch')

    if date_from:
        sales = sales.filter(created_at__date__gte=date_from)
    if date_to:
        sales = sales.filter(created_at__date__lte=date_to)
    if branch_id:
        sales = sales.filter(branch_id=branch_id)
    else:
        thirty_days_ago = timezone.now() - timedelta(days=30)
        sales           = sales.filter(created_at__gte=thirty_days_ago)

    profit_by_day = {}
    for sale in sales:
        day = sale.created_at.strftime('%Y-%m-%d')
        profit_by_day[day] = profit_by_day.get(day, 0) + float(sale.get_total_profit())

    total_profit  = sum(profit_by_day.values())
    total_revenue = sum(float(sale.get_total()) for sale in sales)

    # profit per branch
    branch_totals = []
    for branch in branches:
        branch_sales   = sales.filter(branch=branch)
        branch_revenue = sum(float(s.get_total()) for s in branch_sales)
        branch_profit  = sum(float(s.get_total_profit()) for s in branch_sales)
        branch_totals.append({
            'branch':  branch,
            'revenue': branch_revenue,
            'profit':  branch_profit,
        })

    context = {
        'sales':           sales,
        'profit_by_day':   profit_by_day,
        'total_profit':    total_profit,
        'total_revenue':   total_revenue,
        'branches':        branches,
        'branch_totals':   branch_totals,
        'selected_branch': branch_id,
        'date_from':       date_from or '',
        'date_to':         date_to or '',
    }
    return render(request, 'prototype/reports/profit.html', context)


@admin_required
def report_gold_price(request):
    gold_prices = GoldPrice.objects.order_by('-updated_at')
    latest_gold = gold_prices.first()
    highest     = gold_prices.order_by('-price_per_gram').first()
    lowest      = gold_prices.order_by('price_per_gram').first()

    chart_labels = []
    chart_values = []
    for gp in reversed(list(gold_prices[:30])):
        chart_labels.append(gp.updated_at.strftime('%Y-%m-%d %H:%M'))
        chart_values.append(float(gp.price_per_gram))

    context = {
        'gold_prices':  gold_prices,
        'latest_gold':  latest_gold,
        'highest':      highest,
        'lowest':       lowest,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
    }
    return render(request, 'prototype/reports/gold_price.html', context)


def write_csv_response(filename, rows):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerows(rows)
    return response


@admin_required
def export_sales_csv(request):
    rows = [['Sale ID', 'Customer', 'Branch', 'Subtotal', 'Discount', 'Total', 'Profit', 'Date']]
    sales = Sale.objects.select_related('customer', 'branch').order_by('-created_at')
    for sale in sales:
        rows.append([
            sale.id,
            sale.customer.full_name if sale.customer else sale.customer_name,
            sale.branch.name if sale.branch else '',
            sale.get_subtotal(),
            sale.discount_amount,
            sale.get_total(),
            sale.get_total_profit(),
            sale.created_at.strftime('%Y-%m-%d %H:%M'),
        ])
    return write_csv_response('sales_report.csv', rows)


@admin_required
def export_inventory_csv(request):
    rows = [['Product Code', 'Product', 'Branch', 'Category', 'Karat', 'Weight', 'Quantity', 'Low Stock Threshold']]
    inventory = Inventory.objects.select_related('product', 'product__category', 'branch').order_by('branch', 'product__name')
    for item in inventory:
        rows.append([
            item.product.product_code,
            item.product.name,
            item.branch.name if item.branch else '',
            item.product.category.name,
            item.product.karat,
            item.product.weight_grams,
            item.quantity_pieces,
            item.product.low_stock_threshold,
        ])
    return write_csv_response('inventory_report.csv', rows)


@admin_required
def export_financial_csv(request):
    rows = [['Metric', 'Amount']]
    sales = Sale.objects.all()
    purchases = Purchase.objects.all()
    expenses = Expense.objects.all()
    returns = SaleReturn.objects.all()
    total_revenue = sum(sale.get_total() for sale in sales)
    gross_profit = sum(sale.get_total_profit() for sale in sales)
    purchase_outflow = sum(purchase.get_total_cost() for purchase in purchases)
    expense_outflow = sum(expense.amount for expense in expenses)
    refund_outflow = sum(sale_return.refund_amount for sale_return in returns)
    rows.extend([
        ['Cash In', total_revenue],
        ['Purchase Outflow', purchase_outflow],
        ['Expense Outflow', expense_outflow],
        ['Refund Outflow', refund_outflow],
        ['Net Cash Flow', total_revenue - purchase_outflow - expense_outflow - refund_outflow],
        ['Gross Profit', gross_profit],
        ['Net Profit', gross_profit - expense_outflow - refund_outflow],
    ])
    return write_csv_response('financial_report.csv', rows)

def get_branch_filter(request):
    """
    Admin → no filter (sees all branches)
    Cashier → filter by their branch
    """
    if request.user.profile.is_admin():
        return {}  # no filter
    return {'branch': request.user.profile.branch}
