from django.db import models

class GoldPrice(models.Model):
    price_per_gram = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Gold Price: {self.price_per_gram} @ {self.updated_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "Gold Price"
        verbose_name_plural = "Gold Prices"

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Product(models.Model):
    KARAT_CHOICES = [
        (18, '18K'),
        (21, '21K'),
        (22, '22K'),
        (24, '24K'),
    ]

    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    karat = models.IntegerField(choices=KARAT_CHOICES, default=21)
    weight_grams = models.DecimalField(max_digits=8, decimal_places=3)
    workmanship_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_selling_price(self):
        latest = GoldPrice.objects.order_by('-updated_at').first()
        if latest:
            return (latest.price_per_gram * self.weight_grams) + self.workmanship_fee
        return None

    def __str__(self):
        return f"{self.name} ({self.karat}K - {self.weight_grams}g)"

class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    quantity_pieces = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} — {self.quantity_pieces} pcs"

    class Meta:
        verbose_name_plural = "Inventory"

class Sale(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    customer_name = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    gold_price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total(self):
        return sum(item.get_subtotal() for item in self.items.all()) or 0

    def get_total_profit(self):
        return sum(item.get_profit() for item in self.items.all()) or 0

    def __str__(self):
        return f"Sale #{self.id} — {self.created_at.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):          # ← belongs to Sale
        if not self.gold_price_at_sale:
            latest_gold = GoldPrice.objects.order_by('-updated_at').first()
            if latest_gold:
                self.gold_price_at_sale = latest_gold.price_per_gram
        super().save(*args, **kwargs)

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_per_piece = models.DecimalField(max_digits=10, decimal_places=2)
    cost_per_piece = models.DecimalField(max_digits=10, decimal_places=2)

    def get_subtotal(self):
        if self.price_per_piece is None or self.quantity is None:
            return 0
        return self.price_per_piece * self.quantity

    def get_profit(self):
        if self.price_per_piece is None or self.cost_per_piece is None or self.quantity is None:
            return 0
        return (self.price_per_piece - self.cost_per_piece) * self.quantity

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
    
    def save(self, *args, **kwargs):          # ← belongs to SaleItem
        if self.product:
            latest_gold = GoldPrice.objects.order_by('-updated_at').first()
            if latest_gold:
                gold_price = latest_gold.price_per_gram
                self.cost_per_piece = gold_price * self.product.weight_grams
                self.price_per_piece = self.cost_per_piece + self.product.workmanship_fee
        super().save(*args, **kwargs)