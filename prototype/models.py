from django.db import models
from decimal import Decimal
from uuid import uuid4
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


def generate_product_code():
    return f"PRD-{uuid4().hex[:10].upper()}"


def generate_customer_code():
    return f"CUS-{uuid4().hex[:10].upper()}"


def generate_supplier_code():
    return f"SUP-{uuid4().hex[:10].upper()}"


class Branch(models.Model):
    name       = models.CharField(max_length=200)
    address    = models.TextField(blank=True)
    phone      = models.CharField(max_length=20, blank=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Branches"

class GoldPrice(models.Model):
    price_per_gram = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at     = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Gold Price: {self.price_per_gram} @ {self.updated_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name        = "Gold Price"
        verbose_name_plural = "Gold Prices"


class Category(models.Model):
    name        = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image       = models.ImageField(upload_to='categories/', blank=True, null=True)  # ← add


    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Customer(models.Model):
    CUSTOMER_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('business', 'Business'),
    ]
    STATUS_CHOICES = [
        ('prospect', 'Prospect'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    customer_code      = models.CharField(max_length=32, unique=True, default=generate_customer_code, editable=False)
    full_name          = models.CharField(max_length=200)
    customer_type      = models.CharField(max_length=20, choices=CUSTOMER_TYPE_CHOICES, default='individual')
    status             = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    phone              = models.CharField(max_length=30, blank=True)
    email              = models.EmailField(blank=True)
    address            = models.TextField(blank=True)
    date_of_birth      = models.DateField(blank=True, null=True)
    acquisition_source = models.CharField(max_length=100, blank=True)
    notes              = models.TextField(blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.customer_code})"


class Supplier(models.Model):
    supplier_code  = models.CharField(max_length=32, unique=True, default=generate_supplier_code, editable=False)
    name           = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200, blank=True)
    phone          = models.CharField(max_length=30, blank=True)
    email          = models.EmailField(blank=True)
    address        = models.TextField(blank=True)
    tax_number     = models.CharField(max_length=100, blank=True)
    payment_terms  = models.CharField(max_length=200, blank=True)
    lead_time_days = models.PositiveIntegerField(default=0)
    notes          = models.TextField(blank=True)
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.supplier_code})"


class Product(models.Model):
    KARAT_CHOICES = [
        (24, '24K'),
        (21, '21K'),
        (18, '18K'),
        (14, '14K'),
    ]

    KARAT_PURITY = {
        24: Decimal('1.0'),
        21: Decimal('0.875'),
        18: Decimal('0.75'),
        14: Decimal('0.585'),
    }

    product_code      = models.CharField(max_length=32, unique=True, default=generate_product_code, editable=False)
    sku               = models.CharField(max_length=64, unique=True, blank=True, null=True)
    barcode           = models.CharField(max_length=64, unique=True, blank=True, null=True)
    name              = models.CharField(max_length=200)
    category          = models.ForeignKey(Category, on_delete=models.PROTECT)
    preferred_supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, blank=True, null=True, related_name='products')
    karat             = models.IntegerField(choices=KARAT_CHOICES, default=21)
    weight_grams      = models.DecimalField(max_digits=8, decimal_places=3)
    workmanship_fee   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    low_stock_threshold = models.PositiveIntegerField(default=3)
    image             = models.ImageField(upload_to='products/', blank=True, null=True)
    notes             = models.TextField(blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    def get_purity(self):
        return self.KARAT_PURITY.get(self.karat, Decimal('1.0'))

    def get_selling_price(self):
        latest = GoldPrice.objects.order_by('-updated_at').first()
        if latest:
            return (latest.price_per_gram * self.get_purity() * self.weight_grams) + self.workmanship_fee
        return None

    def get_cost_price(self):
        latest = GoldPrice.objects.order_by('-updated_at').first()
        if latest:
            return latest.price_per_gram * self.get_purity() * self.weight_grams
        return None

    def __str__(self):
        return f"{self.product_code} - {self.name} ({self.karat}K - {self.weight_grams}g)"
    


class Inventory(models.Model):
    product         = models.ForeignKey(Product, on_delete=models.CASCADE)
    branch          = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
    quantity_pieces = models.PositiveIntegerField(default=0)

    def __str__(self):
        branch_name = self.branch.name if self.branch else 'No branch'
        return f"{self.product.name} — {branch_name} — {self.quantity_pieces} pcs"

    class Meta:
        verbose_name_plural = "Inventory"
        unique_together     = ('product', 'branch')


class Sale(models.Model):
    created_at         = models.DateTimeField(auto_now_add=True)
    customer           = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True, related_name='sales')
    customer_name      = models.CharField(max_length=200, blank=True)
    discount_amount    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes              = models.TextField(blank=True)
    gold_price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)
    branch             = models.ForeignKey(Branch, on_delete=models.PROTECT, null=True)

    def get_subtotal(self):
        return sum(item.get_subtotal() for item in self.items.all()) or 0

    def get_total(self):
        return max(self.get_subtotal() - self.discount_amount, Decimal('0'))

    def get_total_profit(self):
        return sum(item.get_profit() for item in self.items.all()) - self.discount_amount

    def save(self, *args, **kwargs):
        if not self.gold_price_at_sale:
            latest_gold = GoldPrice.objects.order_by('-updated_at').first()
            if latest_gold:
                self.gold_price_at_sale = latest_gold.price_per_gram
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Sale #{self.id} — {self.branch} — {self.created_at.strftime('%Y-%m-%d')}"


class CustomerInteraction(models.Model):
    INTERACTION_CHOICES = [
        ('call', 'Call'),
        ('visit', 'Visit'),
        ('message', 'Message'),
        ('email', 'Email'),
        ('complaint', 'Complaint'),
        ('follow_up', 'Follow-up'),
        ('other', 'Other'),
    ]

    customer         = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='interactions')
    branch           = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_CHOICES, default='other')
    subject          = models.CharField(max_length=200)
    notes            = models.TextField(blank=True)
    follow_up_at     = models.DateTimeField(blank=True, null=True)
    created_by       = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.full_name} - {self.subject}"


class SaleItem(models.Model):
    sale            = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product         = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity        = models.PositiveIntegerField(default=1)
    price_per_piece = models.DecimalField(max_digits=10, decimal_places=2)
    cost_per_piece  = models.DecimalField(max_digits=10, decimal_places=2)

    def get_subtotal(self):
        if self.price_per_piece is None or self.quantity is None:
            return 0
        return self.price_per_piece * self.quantity

    def get_profit(self):
        if self.price_per_piece is None or self.cost_per_piece is None or self.quantity is None:
            return 0
        return (self.price_per_piece - self.cost_per_piece) * self.quantity

    def save(self, *args, **kwargs):
        if self.product and (not self.cost_per_piece or not self.price_per_piece):
            latest_gold = GoldPrice.objects.order_by('-updated_at').first()
            if latest_gold:
                gold_price           = latest_gold.price_per_gram
                purity               = self.product.get_purity()
                if not self.cost_per_piece:
                    self.cost_per_piece  = gold_price * purity * self.product.weight_grams
                if not self.price_per_piece:
                    self.price_per_piece = self.cost_per_piece + self.product.workmanship_fee
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"


class SaleReturn(models.Model):
    sale_item     = models.ForeignKey(SaleItem, on_delete=models.PROTECT, related_name='returns')
    branch        = models.ForeignKey(Branch, on_delete=models.PROTECT, null=True)
    quantity      = models.PositiveIntegerField(default=1)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason        = models.TextField(blank=True)
    restock       = models.BooleanField(default=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Return: {self.sale_item.product.name} x{self.quantity}"


class Purchase(models.Model):
    product            = models.ForeignKey(Product, on_delete=models.PROTECT)
    branch             = models.ForeignKey(Branch, on_delete=models.PROTECT, null=True)
    quantity_purchased = models.PositiveIntegerField()
    cost_per_piece     = models.DecimalField(max_digits=10, decimal_places=2)
    supplier           = models.ForeignKey(Supplier, on_delete=models.SET_NULL, blank=True, null=True, related_name='purchases')
    supplier_name      = models.CharField(max_length=200, blank=True)
    notes              = models.TextField(blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)

    def get_total_cost(self):
        return self.cost_per_piece * self.quantity_purchased

    def __str__(self):
        return f"Purchase: {self.product.name} x{self.quantity_purchased} — {self.branch}"


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('rent', 'Rent'),
        ('salary', 'Salary'),
        ('utilities', 'Utilities'),
        ('maintenance', 'Maintenance'),
        ('marketing', 'Marketing'),
        ('other', 'Other'),
    ]

    branch      = models.ForeignKey(Branch, on_delete=models.PROTECT, blank=True, null=True)
    category    = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    description = models.CharField(max_length=255)
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at     = models.DateField()
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_category_display()}: {self.amount}"


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('cashier', 'Cashier'),
    ]

    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cashier')
    branch     = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_admin(self):
        return self.role == 'admin'

    def is_cashier(self):
        return self.role == 'cashier'

    def __str__(self):
        return f"{self.user.username} — {self.role}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
