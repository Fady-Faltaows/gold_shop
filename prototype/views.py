from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from .models import GoldPrice, Category, Product, Inventory, Sale, SaleItem, Purchase, Branch
from .forms import SaleForm, SaleItemForm, GoldPriceForm, PurchaseForm, ProductForm, CategoryForm
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
    low_stock      = Inventory.objects.filter(**branch_filter, quantity_pieces__lte=3)

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
    products = Product.objects.select_related('category').all()
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
        sales    = Sale.objects.order_by('-created_at')
        branches = Branch.objects.filter(is_active=True)
        if branch_id:
            sales = sales.filter(branch_id=branch_id)
    else:
        sales    = Sale.objects.filter(
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
            return redirect('sale_list')

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

# ─────────────────────────────────────────────
# PURCHASES
# ─────────────────────────────────────────────

@admin_required
def purchase_list(request):
    branch_id = request.GET.get('branch')
    purchases = Purchase.objects.select_related('product', 'branch').order_by('-created_at')

    if branch_id:
        purchases = purchases.filter(branch_id=branch_id)

    branches = Branch.objects.filter(is_active=True)

    return render(request, 'prototype/purchase_list.html', {
        'purchases': purchases,
        'branches':  branches,
        'selected_branch': branch_id,
    })


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
            return redirect('purchase_list')
    else:
        form = PurchaseForm()

    return render(request, 'prototype/purchase_create.html', {
        'form':          form,
        'gold_price_js': float(latest_gold.price_per_gram) if latest_gold else 0,
        'products':      products,
        'branches':      branches,
    })


# ─────────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────────

@admin_required
def reports_home(request):
    return render(request, 'prototype/reports/home.html')


@admin_required
def report_sales(request):
    date_from = request.GET.get('date_from')
    date_to   = request.GET.get('date_to')
    branch_id = request.GET.get('branch')
    sales     = Sale.objects.order_by('-created_at')

    if date_from:
        sales = sales.filter(created_at__date__gte=date_from)
    if date_to:
        sales = sales.filter(created_at__date__lte=date_to)
    if branch_id:
        sales = sales.filter(branch_id=branch_id)

    total_revenue = sum(sale.get_total() for sale in sales)
    total_profit  = sum(sale.get_total_profit() for sale in sales)
    total_count   = sales.count()
    branches      = Branch.objects.filter(is_active=True)

    context = {
        'sales':            sales,
        'total_revenue':    total_revenue,
        'total_profit':     total_profit,
        'total_count':      total_count,
        'date_from':        date_from or '',
        'date_to':          date_to or '',
        'branches':         branches,
        'selected_branch':  branch_id,
    }
    return render(request, 'prototype/reports/sales.html', context)


@admin_required
def report_inventory(request):
    inventory    = Inventory.objects.select_related(
        'product', 'product__category'
    ).order_by('quantity_pieces')

    out_of_stock = inventory.filter(quantity_pieces=0)
    low_stock    = inventory.filter(quantity_pieces__gt=0, quantity_pieces__lte=3)
    in_stock     = inventory.filter(quantity_pieces__gt=3)

    context = {
        'inventory':    inventory,
        'out_of_stock': out_of_stock,
        'low_stock':    low_stock,
        'in_stock':     in_stock,
    }
    return render(request, 'prototype/reports/inventory.html', context)


@admin_required
def report_profit(request):
    date_from = request.GET.get('date_from')
    date_to   = request.GET.get('date_to')
    branch_id = request.GET.get('branch')
    sales     = Sale.objects.order_by('created_at')

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
    branches      = Branch.objects.filter(is_active=True)

    context = {
        'sales':           sales,
        'profit_by_day':   profit_by_day,
        'total_profit':    total_profit,
        'total_revenue':   total_revenue,
        'date_from':       date_from or '',
        'date_to':         date_to or '',
        'branches':        branches,
        'selected_branch': branch_id,
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

def get_branch_filter(request):
    """
    Admin → no filter (sees all branches)
    Cashier → filter by their branch
    """
    if request.user.profile.is_admin():
        return {}  # no filter
    return {'branch': request.user.profile.branch}