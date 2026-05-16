from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from prototype.models import Branch, Category, Product, Inventory, GoldPrice, Sale
from .models import Order, OrderItem, OnlinePurchase

class StoreTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.branch = Branch.objects.create(name='Main Branch', is_active=True)
        self.category = Category.objects.create(name='Rings')
        self.product = Product.objects.create(
            name='Test Ring',
            category=self.category,
            karat=21,
            weight_grams=Decimal('5.00'),
            workmanship_fee=Decimal('100.00'),
            sku='T-RING-01'
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            branch=self.branch,
            quantity_pieces=10
        )
        self.gold_price = GoldPrice.objects.create(price_per_gram=Decimal('3000.00'))

    def test_home_page_loads(self):
        response = self.client.get(reverse('store:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Ring')

    def test_product_detail_page(self):
        response = self.client.get(reverse('store:product_detail', args=[self.product.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Ring')
        self.assertContains(response, 'In Stock')

    def test_cart_operations(self):
        # Add to cart
        response = self.client.post(reverse('store:cart_add', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        
        # Check cart view
        response = self.client.get(reverse('store:cart_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Ring')
        self.assertContains(response, '1') # Quantity

        # Add more
        self.client.post(reverse('store:cart_add', args=[self.product.id]))
        response = self.client.get(reverse('store:cart_view'))
        self.assertContains(response, '2') # Quantity

        # Remove from cart
        self.client.post(reverse('store:cart_remove', args=[self.product.id]))
        response = self.client.get(reverse('store:cart_view'))
        self.assertNotContains(response, 'Test Ring')

    def test_checkout_process(self):
        # Setup cart
        session = self.client.session
        session['cart'] = {str(self.product.id): 2}
        session.save()

        # Submit checkout
        response = self.client.post(reverse('store:checkout'), {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '123456789',
            'address': '123 Test St'
        })

        self.assertEqual(response.status_code, 302)
        
        # Verify Order
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertEqual(order.customer_name, 'John Doe')
        self.assertEqual(order.total_amount, self.product.get_selling_price() * 2)

        # Verify Inventory deduction
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity_pieces, 8)

        # Verify management Sale creation
        sale = Sale.objects.first()
        self.assertIsNotNone(sale)
        self.assertEqual(sale.items.first().product, self.product)
        self.assertEqual(sale.items.first().quantity, 2)

    def test_sell_gold_request(self):
        response = self.client.post(reverse('store:sell_gold'), {
            'name': 'Jane Seller',
            'phone': '987654321',
            'email': 'jane@example.com',
            'gold_type': 'Broken Ring',
            'karat': '18',
            'weight': '4.5',
            'notes': 'Need cash'
        })

        self.assertEqual(response.status_code, 302)
        
        # Verify OnlinePurchase
        purchase_request = OnlinePurchase.objects.first()
        self.assertIsNotNone(purchase_request)
        self.assertEqual(purchase_request.customer_name, 'Jane Seller')
        self.assertEqual(purchase_request.karat, 18)
        self.assertEqual(purchase_request.estimated_weight, Decimal('4.5'))

    def test_cart_add_respects_stock_limits(self):
        # Set stock to 1
        self.inventory.quantity_pieces = 1
        self.inventory.save()

        # Add 1
        self.client.post(reverse('store:cart_add', args=[self.product.id]))
        # Try to add another
        response = self.client.post(reverse('store:cart_add', args=[self.product.id]))
        
        # Should redirect back to cart view with error
        self.assertEqual(response.status_code, 302)
        
        # Check session
        session = self.client.session
        self.assertEqual(session['cart'][str(self.product.id)], 1)
