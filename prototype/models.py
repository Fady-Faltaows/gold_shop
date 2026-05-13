from django.db import models
from decimal import Decimal
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


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

    name            = models.CharField(max_length=200)
    category        = models.ForeignKey(Category, on_delete=models.PROTECT)
    karat           = models.IntegerField(choices=KARAT_CHOICES, default=21)
    weight_grams    = models.DecimalField(max_digits=8, decimal_places=3)
    workmanship_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image           = models.ImageField(upload_to='products/', blank=True, null=True)
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

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
        return f"{self.name} ({self.karat}K - {self.weight_grams}g)"
    


class Inventory(models.Model):
    product         = models.ForeignKey(Product, on_delete=models.CASCADE)
    branch          = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
    quantity_pieces = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} — {self.branch.name} — {self.quantity_pieces} pcs"

    class Meta:
        verbose_name_plural = "Inventory"
        unique_together     = ('product', 'branch')


class Sale(models.Model):
    created_at         = models.DateTimeField(auto_now_add=True)
    customer_name      = models.CharField(max_length=200, blank=True)
    notes              = models.TextField(blank=True)
    gold_price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)
    branch             = models.ForeignKey(Branch, on_delete=models.PROTECT, null=True)

    def get_total(self):
        return sum(item.get_subtotal() for item in self.items.all()) or 0

    def get_total_profit(self):
        return sum(item.get_profit() for item in self.items.all()) or 0

    def save(self, *args, **kwargs):
        if not self.gold_price_at_sale:
            latest_gold = GoldPrice.objects.order_by('-updated_at').first()
            if latest_gold:
                self.gold_price_at_sale = latest_gold.price_per_gram
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Sale #{self.id} — {self.branch} — {self.created_at.strftime('%Y-%m-%d')}"


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
        if self.product:
            latest_gold = GoldPrice.objects.order_by('-updated_at').first()
            if latest_gold:
                gold_price           = latest_gold.price_per_gram
                purity               = self.product.get_purity()
                self.cost_per_piece  = gold_price * purity * self.product.weight_grams
                self.price_per_piece = self.cost_per_piece + self.product.workmanship_fee
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

class Purchase(models.Model):
    product            = models.ForeignKey(Product, on_delete=models.PROTECT)
    branch             = models.ForeignKey(Branch, on_delete=models.PROTECT, null=True)
    quantity_purchased = models.PositiveIntegerField()
    cost_per_piece     = models.DecimalField(max_digits=10, decimal_places=2)
    supplier_name      = models.CharField(max_length=200, blank=True)
    notes              = models.TextField(blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)

    def get_total_cost(self):
        return self.cost_per_piece * self.quantity_purchased

    def __str__(self):
        return f"Purchase: {self.product.name} x{self.quantity_purchased} — {self.branch}"

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