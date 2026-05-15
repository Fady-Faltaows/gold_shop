from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import ExpenseForm, ProductForm, SaleForm, SupplierForm
from .models import (
    Branch,
    Category,
    Customer,
    Expense,
    GoldPrice,
    Inventory,
    Product,
    Purchase,
    Sale,
    SaleItem,
    SaleReturn,
    Supplier,
)


class GoldShopTestMixin:
    def setUp(self):
        self.branch = Branch.objects.create(name='Main Branch')
        self.admin = User.objects.create_user(username='admin', password='pass12345')
        self.admin.profile.role = 'admin'
        self.admin.profile.branch = self.branch
        self.admin.profile.save()
        self.cashier = User.objects.create_user(username='cashier', password='pass12345')
        self.cashier.profile.role = 'cashier'
        self.cashier.profile.branch = self.branch
        self.cashier.profile.save()
        self.category = Category.objects.create(name='Rings')
        self.supplier = Supplier.objects.create(name='Trusted Supplier')
        self.customer = Customer.objects.create(full_name='Nora Customer')
        self.gold_price = GoldPrice.objects.create(price_per_gram=Decimal('3000.00'))
        self.product = Product.objects.create(
            name='Wedding Ring',
            category=self.category,
            preferred_supplier=self.supplier,
            karat=21,
            weight_grams=Decimal('10.000'),
            workmanship_fee=Decimal('500.00'),
            low_stock_threshold=3,
            sku='RING-001',
            barcode='BAR-001',
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            branch=self.branch,
            quantity_pieces=5,
        )


class ModelTests(GoldShopTestMixin, TestCase):
    def test_product_pricing_uses_latest_gold_price_and_purity(self):
        self.assertEqual(self.product.get_purity(), Decimal('0.875'))
        self.assertEqual(self.product.get_cost_price(), Decimal('26250.000000'))
        self.assertEqual(self.product.get_selling_price(), Decimal('26750.000000'))

    def test_sale_totals_include_discount_and_do_not_go_below_zero(self):
        sale = Sale.objects.create(
            customer=self.customer,
            gold_price_at_sale=self.gold_price.price_per_gram,
            branch=self.branch,
            discount_amount=Decimal('100.00'),
        )
        SaleItem.objects.create(
            sale=sale,
            product=self.product,
            quantity=2,
            price_per_piece=Decimal('0'),
            cost_per_piece=Decimal('0'),
        )

        self.assertEqual(sale.get_subtotal(), Decimal('53500.000000'))
        self.assertEqual(sale.get_total(), Decimal('53400.000000'))
        self.assertEqual(sale.get_total_profit(), Decimal('900.000000'))

        sale.discount_amount = Decimal('999999.00')
        self.assertEqual(sale.get_total(), Decimal('0'))

    def test_purchase_total_cost(self):
        purchase = Purchase.objects.create(
            product=self.product,
            branch=self.branch,
            supplier=self.supplier,
            quantity_purchased=3,
            cost_per_piece=Decimal('26250.00'),
        )

        self.assertEqual(purchase.get_total_cost(), Decimal('78750.00'))

    def test_user_profile_is_created_automatically(self):
        user = User.objects.create_user(username='new-user', password='pass12345')

        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.role, 'cashier')

    def test_inventory_str_handles_missing_branch_safely(self):
        inventory = Inventory.objects.create(product=self.product, branch=None, quantity_pieces=1)

        self.assertIn(self.product.name, str(inventory))


class FormTests(GoldShopTestMixin, TestCase):
    def test_product_form_accepts_empty_optional_unique_identifiers(self):
        form = ProductForm(data={
            'name': 'Bracelet',
            'category': self.category.id,
            'karat': 18,
            'weight_grams': '5.000',
            'workmanship_fee': '150.00',
            'low_stock_threshold': 2,
            'sku': '',
            'barcode': '',
            'notes': '',
            'preferred_supplier': '',
        })

        self.assertTrue(form.is_valid(), form.errors)
        product = form.save()
        self.assertIsNone(product.sku)
        self.assertIsNone(product.barcode)

    def test_sale_form_allows_existing_customer_and_discount(self):
        form = SaleForm(data={
            'customer': self.customer.id,
            'customer_name': '',
            'discount_amount': '25.00',
            'notes': 'VIP',
        })

        self.assertTrue(form.is_valid(), form.errors)

    def test_supplier_form_rejects_negative_lead_time(self):
        form = SupplierForm(data={
            'name': 'Bad Supplier',
            'lead_time_days': -1,
            'is_active': 'on',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('lead_time_days', form.errors)

    def test_expense_form_requires_valid_date_and_amount(self):
        form = ExpenseForm(data={
            'branch': self.branch.id,
            'category': 'rent',
            'description': 'Store rent',
            'amount': '1200.00',
            'paid_at': '2026-05-15',
            'notes': '',
        })

        self.assertTrue(form.is_valid(), form.errors)


class AuthAndViewTests(GoldShopTestMixin, TestCase):
    def test_anonymous_user_is_redirected_from_dashboard(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_cashier_cannot_access_admin_only_pages(self):
        self.client.login(username='cashier', password='pass12345')

        response = self.client.get(reverse('product_list'))

        self.assertRedirects(response, reverse('access_denied'))

    def test_admin_can_update_gold_price_from_dashboard(self):
        self.client.login(username='admin', password='pass12345')

        response = self.client.post(reverse('dashboard'), {'price_per_gram': '3200.00'})

        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(GoldPrice.objects.latest('updated_at').price_per_gram, Decimal('3200.00'))

    def test_sale_create_decrements_inventory_and_redirects_to_receipt(self):
        self.client.login(username='cashier', password='pass12345')

        response = self.client.post(reverse('sale_create'), {
            'customer': self.customer.id,
            'customer_name': '',
            'discount_amount': '50.00',
            'notes': '',
            'product': [self.product.id],
            'quantity': ['2'],
        })

        sale = Sale.objects.latest('id')
        self.assertRedirects(response, reverse('sale_receipt', args=[sale.id]))
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity_pieces, 3)
        self.assertEqual(sale.customer_name, self.customer.full_name)
        self.assertEqual(sale.items.count(), 1)

    def test_sale_create_rejects_insufficient_stock_and_rolls_back_sale(self):
        self.client.login(username='cashier', password='pass12345')

        response = self.client.post(reverse('sale_create'), {
            'customer': '',
            'customer_name': 'Walk In',
            'discount_amount': '0',
            'notes': '',
            'product': [self.product.id],
            'quantity': ['99'],
        })

        self.assertRedirects(response, reverse('sale_create'))
        self.assertEqual(Sale.objects.count(), 0)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity_pieces, 5)

    def test_sale_create_rejects_empty_cart(self):
        self.client.login(username='cashier', password='pass12345')

        response = self.client.post(reverse('sale_create'), {
            'customer': '',
            'customer_name': 'Walk In',
            'discount_amount': '0',
            'notes': '',
            'product': [''],
            'quantity': [''],
        })

        self.assertRedirects(response, reverse('sale_create'))
        self.assertEqual(Sale.objects.count(), 0)

    def test_purchase_create_increments_inventory_and_redirects_to_invoice(self):
        self.client.login(username='admin', password='pass12345')

        response = self.client.post(reverse('purchase_create'), {
            'product': self.product.id,
            'quantity_purchased': '4',
            'supplier': self.supplier.id,
            'supplier_name': '',
            'notes': '',
            'branch': self.branch.id,
        })

        purchase = Purchase.objects.latest('id')
        self.assertRedirects(response, reverse('purchase_invoice', args=[purchase.id]))
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity_pieces, 9)
        self.assertEqual(purchase.supplier_name, self.supplier.name)

    def test_return_restock_increases_inventory(self):
        sale = Sale.objects.create(
            gold_price_at_sale=self.gold_price.price_per_gram,
            branch=self.branch,
        )
        sale_item = SaleItem.objects.create(
            sale=sale,
            product=self.product,
            quantity=2,
            price_per_piece=Decimal('0'),
            cost_per_piece=Decimal('0'),
        )
        self.client.login(username='admin', password='pass12345')

        response = self.client.post(reverse('sale_return_create', args=[sale.id]), {
            'sale_item': sale_item.id,
            'quantity': '1',
            'refund_amount': '26750.00',
            'restock': 'on',
            'reason': 'Customer return',
        })

        self.assertRedirects(response, reverse('sale_list'))
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity_pieces, 6)
        self.assertEqual(SaleReturn.objects.count(), 1)

    def test_return_cannot_exceed_remaining_quantity(self):
        sale = Sale.objects.create(
            gold_price_at_sale=self.gold_price.price_per_gram,
            branch=self.branch,
        )
        sale_item = SaleItem.objects.create(
            sale=sale,
            product=self.product,
            quantity=2,
            price_per_piece=Decimal('0'),
            cost_per_piece=Decimal('0'),
        )
        SaleReturn.objects.create(
            sale_item=sale_item,
            branch=self.branch,
            quantity=1,
            refund_amount=Decimal('26750.00'),
        )
        self.client.login(username='admin', password='pass12345')

        response = self.client.post(reverse('sale_return_create', args=[sale.id]), {
            'sale_item': sale_item.id,
            'quantity': '2',
            'refund_amount': '53500.00',
            'restock': 'on',
            'reason': 'Customer return',
        })

        self.assertRedirects(response, reverse('sale_return_create', args=[sale.id]))
        self.assertEqual(SaleReturn.objects.count(), 1)

    def test_exports_return_csv(self):
        self.client.login(username='admin', password='pass12345')

        response = self.client.get(reverse('export_inventory_csv'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('inventory_report.csv', response['Content-Disposition'])
        self.assertIn(b'Product Code', response.content)

    def test_low_stock_threshold_is_used_on_inventory_report(self):
        self.client.login(username='admin', password='pass12345')
        self.product.low_stock_threshold = 6
        self.product.save()

        response = self.client.get(reverse('report_inventory'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Low Stock')
