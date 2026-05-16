from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum
from prototype.models import Product, Category, GoldPrice, Inventory, Sale, SaleItem, Branch
from .models import Order, OrderItem, OnlinePurchase
from decimal import Decimal

def get_available_products():
    """Helper to get products that have stock in at least one branch."""
    product_ids_in_stock = Inventory.objects.filter(quantity_pieces__gt=0).values_list('product_id', flat=True).distinct()
    return Product.objects.filter(id__in=product_ids_in_stock)

def home(request):
    categories = Category.objects.all()[:4]
    # Only show products in stock
    featured_products = get_available_products()[:8]
    return render(request, 'store/home.html', {
        'categories': categories,
        'featured_products': featured_products,
    })

def product_list(request):
    products = get_available_products()
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    return render(request, 'store/product_list.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    # Check total stock
    total_stock = Inventory.objects.filter(product=product).aggregate(total=Sum('quantity_pieces'))['total'] or 0
    return render(request, 'store/product_detail.html', {
        'product': product,
        'is_in_stock': total_stock > 0,
        'stock_count': total_stock
    })

def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Re-verify stock before adding
    total_stock = Inventory.objects.filter(product=product).aggregate(total=Sum('quantity_pieces'))['total'] or 0
    
    if total_stock <= 0:
        messages.error(request, f"Sorry, {product.name} is currently out of stock.")
        return redirect('store:product_list')

    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    
    current_qty = cart.get(product_id_str, 0)
    if current_qty >= total_stock:
        messages.error(request, f"Cannot add more of {product.name}. Only {total_stock} available.")
    else:
        cart[product_id_str] = current_qty + 1
        request.session['cart'] = cart
        messages.success(request, f"{product.name} added to your selection.")
    
    return redirect('store:cart_view')

def cart_remove(request, item_id):
    cart = request.session.get('cart', {})
    product_id_str = str(item_id)
    if product_id_str in cart:
        del cart[product_id_str]
        request.session['cart'] = cart
        messages.success(request, "Item removed from selection.")
    return redirect('store:cart_view')

def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    grand_total = 0
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        price = product.get_selling_price() or 0
        subtotal = price * quantity
        grand_total += subtotal
        cart_items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
    return render(request, 'store/cart.html', {'cart_items': cart_items, 'grand_total': grand_total})

def sell_gold(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        gold_type = request.POST.get('gold_type')
        karat = request.POST.get('karat')
        weight = request.POST.get('weight')
        notes = request.POST.get('notes')
        image = request.FILES.get('image')

        OnlinePurchase.objects.create(
            customer_name=name,
            phone=phone,
            email=email,
            gold_type=gold_type,
            karat=karat,
            estimated_weight=weight,
            notes=notes,
            image=image
        )
        messages.success(request, "Your valuation request has been submitted. Our experts will contact you soon.")
        return redirect('store:home')

    return render(request, 'store/sell_gold.html')

def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('store:product_list')
        
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        # 1. Create the Store Order
        order = Order.objects.create(
            customer_name=name, email=email, phone=phone, address=address, status='confirmed'
        )
        
        # 2. Create a management Sale to sync with reports
        # We'll use the first active branch as the fulfillment branch for online orders
        fulfillment_branch = Branch.objects.filter(is_active=True).first()
        latest_gold = GoldPrice.objects.order_by('-updated_at').first()
        
        sale = Sale.objects.create(
            customer_name=f"Online: {name}",
            notes=f"Web Order #{order.id}",
            gold_price_at_sale=latest_gold.price_per_gram if latest_gold else 0,
            branch=fulfillment_branch
        )
        
        total = 0
        for product_id, quantity in cart.items():
            product = Product.objects.get(id=product_id)
            price = product.get_selling_price() or 0
            
            # Create OrderItem
            OrderItem.objects.create(order=order, product=product, quantity=quantity, price_at_order=price)
            
            # Create SaleItem (Management sync)
            SaleItem.objects.create(
                sale=sale, product=product, quantity=quantity,
                price_per_piece=price, cost_per_piece=product.get_cost_price() or 0
            )
            
            # 3. Deduct from Inventory (Fulfillment branch)
            inv = Inventory.objects.filter(product=product, branch=fulfillment_branch).first()
            if inv:
                inv.quantity_pieces = max(0, inv.quantity_pieces - quantity)
                inv.save()
            
            total += price * quantity
            
        order.total_amount = total
        order.save()
        
        request.session['cart'] = {}
        messages.success(request, f"Thank you! Your order #{order.id} is confirmed and reflected in our records.")
        return redirect('store:home')

    return render(request, 'store/checkout.html')
