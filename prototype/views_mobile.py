"""
views_mobile.py
Read-only, admin-only views powering the PWA mobile monitor.
"""

from django.db import models
from django.shortcuts import render
from django.utils import timezone
from datetime import datetime, time

from .decorators import admin_required
from .models import (
    Branch, GoldPrice, Inventory, Sale,
    Purchase, Expense, SaleReturn,
)

def get_today_range():
    """Helper to get start and end of day in the current timezone."""
    today = timezone.localtime(timezone.now()).date()
    start = timezone.make_aware(datetime.combine(today, time.min))
    end = timezone.make_aware(datetime.combine(today, time.max))
    return start, end, today

@admin_required
def mobile_dashboard(request):
    start, end, today = get_today_range()
    
    latest_gold = GoldPrice.objects.order_by('-updated_at').first()
    branches    = Branch.objects.filter(is_active=True)

    # Use range instead of __date to be more robust across different DB engines (MySQL/SQLite)
    today_sales   = Sale.objects.filter(created_at__range=(start, end))
    today_revenue = sum(s.get_total()        for s in today_sales)
    today_profit  = sum(s.get_total_profit() for s in today_sales)
    today_count   = today_sales.count()

    low_stock_count = Inventory.objects.filter(
        quantity_pieces__lte=models.F('product__low_stock_threshold'),
        quantity_pieces__gt=0,
    ).count()

    out_of_stock_count = Inventory.objects.filter(quantity_pieces=0).count()

    branch_cards = []
    for branch in branches:
        b_sales   = today_sales.filter(branch=branch)
        b_revenue = sum(s.get_total()        for s in b_sales)
        b_profit  = sum(s.get_total_profit() for s in b_sales)
        b_low     = Inventory.objects.filter(
            branch=branch,
            quantity_pieces__lte=models.F('product__low_stock_threshold'),
        ).count()
        branch_cards.append({
            'branch':  branch,
            'revenue': b_revenue,
            'profit':  b_profit,
            'count':   b_sales.count(),
            'low':     b_low,
        })

    gold_history = list(GoldPrice.objects.order_by('-updated_at')[:14])
    gold_labels  = [g.updated_at.strftime('%d/%m') for g in reversed(gold_history)]
    gold_values  = [float(g.price_per_gram)         for g in reversed(gold_history)]

    context = {
        'latest_gold':         latest_gold,
        'today_revenue':       today_revenue,
        'today_profit':        today_profit,
        'today_count':         today_count,
        'low_stock_count':     low_stock_count,
        'out_of_stock_count':  out_of_stock_count,
        'branch_cards':        branch_cards,
        'gold_labels':         gold_labels,
        'gold_values':         gold_values,
        'today':               today,
    }
    return render(request, 'mobile/dashboard.html', context)

@admin_required
def mobile_inventory(request):
    branch_id = request.GET.get('branch')
    branches  = Branch.objects.filter(is_active=True)

    inventory = Inventory.objects.select_related(
        'product', 'product__category', 'branch'
    ).order_by('branch__name', 'quantity_pieces')

    if branch_id:
        inventory = inventory.filter(branch_id=branch_id)

    out_of_stock = inventory.filter(quantity_pieces=0)
    low_stock    = inventory.filter(
        quantity_pieces__gt=0,
        quantity_pieces__lte=models.F('product__low_stock_threshold'),
    )
    in_stock = inventory.filter(
        quantity_pieces__gt=models.F('product__low_stock_threshold')
    )

    context = {
        'branches':        branches,
        'selected_branch': branch_id,
        'out_of_stock':    out_of_stock,
        'low_stock':       low_stock,
        'in_stock':        in_stock,
        'total':           inventory.count(),
    }
    return render(request, 'mobile/inventory.html', context)

@admin_required
def mobile_sales(request):
    branch_id = request.GET.get('branch')
    branches  = Branch.objects.filter(is_active=True)
    start, end, today = get_today_range()

    sales = Sale.objects.select_related(
        'customer', 'branch'
    ).prefetch_related('items__product').order_by('-created_at')

    if branch_id:
        sales = sales.filter(branch_id=branch_id)

    recent_sales  = sales[:50]
    today_sales   = sales.filter(created_at__range=(start, end))
    today_revenue = sum(s.get_total()        for s in today_sales)
    today_profit  = sum(s.get_total_profit() for s in today_sales)

    context = {
        'sales':           recent_sales,
        'branches':        branches,
        'selected_branch': branch_id,
        'today_revenue':   today_revenue,
        'today_profit':    today_profit,
        'today_count':     today_sales.count(),
    }
    return render(request, 'mobile/sales.html', context)

@admin_required
def mobile_gold_price(request):
    gold_prices = GoldPrice.objects.order_by('-updated_at')[:30]
    latest      = gold_prices[0] if gold_prices else None
    prices_list = list(gold_prices)

    highest = max(prices_list, key=lambda g: g.price_per_gram) if prices_list else None
    lowest  = min(prices_list, key=lambda g: g.price_per_gram) if prices_list else None

    chart_labels = [g.updated_at.strftime('%d/%m %H:%M') for g in reversed(prices_list)]
    chart_values = [float(g.price_per_gram)               for g in reversed(prices_list)]

    change_pct = None
    if len(prices_list) >= 2:
        prev = float(prices_list[1].price_per_gram)
        curr = float(prices_list[0].price_per_gram)
        if prev:
            change_pct = round(((curr - prev) / prev) * 100, 2)

    context = {
        'latest':       latest,
        'gold_prices':  prices_list,
        'highest':      highest,
        'lowest':       lowest,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'change_pct':   change_pct,
    }
    return render(request, 'mobile/gold_price.html', context)

@admin_required
def mobile_reports(request):
    branch_id = request.GET.get('branch')
    date_from = request.GET.get('date_from')
    date_to   = request.GET.get('date_to')
    branches  = Branch.objects.filter(is_active=True)

    today = timezone.localtime(timezone.now()).date()
    if not date_from:
        date_from = today.replace(day=1).isoformat()
    if not date_to:
        date_to = today.isoformat()

    # Convert ISO dates to aware datetimes for range queries
    dt_from = timezone.make_aware(datetime.combine(datetime.fromisoformat(date_from).date(), time.min))
    dt_to   = timezone.make_aware(datetime.combine(datetime.fromisoformat(date_to).date(), time.max))

    sales     = Sale.objects.filter(created_at__range=(dt_from, dt_to))
    purchases = Purchase.objects.filter(created_at__range=(dt_from, dt_to))
    
    # Expenses use DateField so __gte/__lte is fine, but for consistency:
    expenses  = Expense.objects.filter(paid_at__gte=date_from, paid_at__lte=date_to)
    returns   = SaleReturn.objects.filter(created_at__range=(dt_from, dt_to))

    if branch_id:
        sales     = sales.filter(branch_id=branch_id)
        purchases = purchases.filter(branch_id=branch_id)
        expenses  = expenses.filter(branch_id=branch_id)
        returns   = returns.filter(branch_id=branch_id)

    total_revenue    = sum(s.get_total()        for s in sales)
    gross_profit     = sum(s.get_total_profit() for s in sales)
    purchase_outflow = sum(p.get_total_cost()   for p in purchases)
    expense_outflow  = sum(e.amount             for e in expenses)
    refund_outflow   = sum(r.refund_amount      for r in returns)

    cash_in    = total_revenue
    cash_out   = purchase_outflow + expense_outflow + refund_outflow
    net_flow   = cash_in - cash_out
    net_profit = gross_profit - expense_outflow - refund_outflow

    branch_rows = []
    for branch in branches:
        b_sales   = sales.filter(branch=branch)
        b_revenue = sum(s.get_total()        for s in b_sales)
        b_profit  = sum(s.get_total_profit() for s in b_sales)
        branch_rows.append({
            'branch':  branch,
            'revenue': b_revenue,
            'profit':  b_profit,
            'count':   b_sales.count(),
        })

    context = {
        'branches':          branches,
        'selected_branch':   branch_id,
        'date_from':         date_from,
        'date_to':           date_to,
        'total_revenue':     total_revenue,
        'gross_profit':      gross_profit,
        'purchase_outflow':  purchase_outflow,
        'expense_outflow':   expense_outflow,
        'refund_outflow':    refund_outflow,
        'cash_in':           cash_in,
        'cash_out':          cash_out,
        'net_flow':          net_flow,
        'net_profit':        net_profit,
        'branch_rows':       branch_rows,
        'sale_count':        sales.count(),
    }
    return render(request, 'mobile/reports.html', context)