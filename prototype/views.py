from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import GoldPrice, Product, Inventory, Sale, SaleItem, Purchase
from .forms import SaleForm, SaleItemForm, GoldPriceForm, PurchaseForm


def dashboard(request):
    latest_gold = GoldPrice.objects.order_by('-updated_at').first()
    total_products = Product.objects.count()
    total_sales = Sale.objects.count()
    total_profit = sum(sale.get_total_profit() for sale in Sale.objects.all())
    low_stock = Inventory.objects.filter(quantity_pieces__lte=3)

    if request.method == 'POST':
        form = GoldPriceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Gold price updated successfully!')
            return redirect('dashboard')
    else:
        form = GoldPriceForm()

    context = {
        'latest_gold': latest_gold,
        'total_products': total_products,
        'total_sales': total_sales,
        'total_profit': total_profit,
        'low_stock': low_stock,
        'gold_form': form,
    }
    return render(request, 'prototype/dashboard.html', context)


def product_list(request):
    products = Product.objects.select_related('category').all()
    return render(request, 'prototype/product_list.html', {'products': products})


def inventory_list(request):
    inventory = Inventory.objects.select_related('product').all()
    return render(request, 'prototype/inventory_list.html', {'inventory': inventory})


def sale_list(request):
    sales = Sale.objects.order_by('-created_at')
    return render(request, 'prototype/sale_list.html', {'sales': sales})


def sale_create(request):
    latest_gold = GoldPrice.objects.order_by('-updated_at').first()
    products = Product.objects.select_related('category', 'inventory').all()

    if request.method == 'POST':
        sale_form = SaleForm(request.POST)
        if sale_form.is_valid():
            sale = sale_form.save(commit=False)
            if latest_gold:
                sale.gold_price_at_sale = latest_gold.price_per_gram
            else:
                messages.error(request, '⚠️ Cannot create sale — no gold price set!')
                return redirect('sale_create')
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

                        inventory = Inventory.objects.get(product=product)

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
                        pass

            if has_error:
                sale.delete()
                return redirect('sale_create')

            messages.success(request, f'✅ Sale #{sale.id} created successfully!')
            return redirect('sale_list')

    else:
        sale_form = SaleForm()

    context = {
        'sale_form': sale_form,
        'products': products,
        'latest_gold': latest_gold,
        'gold_price_js': float(latest_gold.price_per_gram) if latest_gold else 0,
    }
    return render(request, 'prototype/sale_create.html', context)


def purchase_list(request):
    purchases = Purchase.objects.select_related('product').order_by('-created_at')
    return render(request, 'prototype/purchase_list.html', {'purchases': purchases})


def purchase_create(request):
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save()
            inventory, created = Inventory.objects.get_or_create(
                product=purchase.product,
                defaults={'quantity_pieces': 0}
            )
            inventory.quantity_pieces += purchase.quantity_purchased
            inventory.save()
            messages.success(
                request,
                f'✅ Added {purchase.quantity_purchased} pieces of '
                f'{purchase.product.name} to inventory!'
            )
            return redirect('purchase_list')
    else:
        form = PurchaseForm()

    return render(request, 'prototype/purchase_create.html', {'form': form})


def reports_home(request):
    return render(request, 'prototype/reports/home.html')


def report_sales(request):
    date_from = request.GET.get('date_from')
    date_to   = request.GET.get('date_to')
    sales     = Sale.objects.order_by('-created_at')

    if date_from:
        sales = sales.filter(created_at__date__gte=date_from)
    if date_to:
        sales = sales.filter(created_at__date__lte=date_to)

    total_revenue = sum(sale.get_total() for sale in sales)
    total_profit  = sum(sale.get_total_profit() for sale in sales)
    total_count   = sales.count()

    context = {
        'sales': sales,
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'total_count': total_count,
        'date_from': date_from or '',
        'date_to': date_to or '',
    }
    return render(request, 'prototype/reports/sales.html', context)


def report_inventory(request):
    inventory   = Inventory.objects.select_related(
        'product', 'product__category'
    ).order_by('quantity_pieces')

    out_of_stock = inventory.filter(quantity_pieces=0)
    low_stock    = inventory.filter(quantity_pieces__gt=0, quantity_pieces__lte=3)
    in_stock     = inventory.filter(quantity_pieces__gt=3)

    context = {
        'inventory': inventory,
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'in_stock': in_stock,
    }
    return render(request, 'prototype/reports/inventory.html', context)


def report_profit(request):
    date_from = request.GET.get('date_from')
    date_to   = request.GET.get('date_to')
    sales     = Sale.objects.order_by('created_at')

    if date_from:
        sales = sales.filter(created_at__date__gte=date_from)
    if date_to:
        sales = sales.filter(created_at__date__lte=date_to)
    else:
        thirty_days_ago = timezone.now() - timedelta(days=30)
        sales = sales.filter(created_at__gte=thirty_days_ago)

    profit_by_day = {}
    for sale in sales:
        day = sale.created_at.strftime('%Y-%m-%d')
        profit_by_day[day] = profit_by_day.get(day, 0) + float(sale.get_total_profit())

    total_profit  = sum(profit_by_day.values())
    total_revenue = sum(float(sale.get_total()) for sale in sales)

    context = {
        'sales': sales,
        'profit_by_day': profit_by_day,
        'total_profit': total_profit,
        'total_revenue': total_revenue,
        'date_from': date_from or '',
        'date_to': date_to or '',
    }
    return render(request, 'prototype/reports/profit.html', context)