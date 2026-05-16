from django.db import models
from prototype.models import Product

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    customer_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_order = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class OnlinePurchase(models.Model):
    """Represents a customer selling gold to the shop online."""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('offered', 'Offer Sent'),
        ('accepted', 'Accepted'),
        ('item_received', 'Item Received'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    KARAT_CHOICES = [
        (18, '18K'),
        (21, '21K'),
        (22, '22K'),
        (24, '24K'),
    ]
    customer_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    gold_type = models.CharField(max_length=100, help_text="e.g., Broken Ring, Scrap, Coin")
    karat = models.IntegerField(choices=KARAT_CHOICES)
    estimated_weight = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='online_purchases/', blank=True, null=True)
    notes = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shop_offer_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Purchase Request #{self.id} - {self.customer_name} ({self.gold_type})"
