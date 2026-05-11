from django.contrib import admin
from .models import GoldPrice, Category, Product, Inventory, Sale, SaleItem, Purchase

@admin.register(GoldPrice)
class GoldPriceAdmin(admin.ModelAdmin):
    list_display = ('price_per_gram', 'updated_at')
    ordering = ('-updated_at',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'karat', 'weight_grams', 'workmanship_fee', 'get_selling_price')
    list_filter = ('karat', 'category')
    search_fields = ('name',)
    ordering = ('category', 'name')

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity_pieces')
    search_fields = ('product__name',)
    ordering = ('product',)

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    fields = ('product', 'quantity', 'price_per_piece', 'cost_per_piece', 'get_subtotal', 'get_profit')
    readonly_fields = ('price_per_piece', 'cost_per_piece', 'get_subtotal', 'get_profit')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'gold_price_at_sale', 'get_total', 'get_total_profit', 'created_at')
    search_fields = ('customer_name',)
    ordering = ('-created_at',)
    readonly_fields = ('gold_price_at_sale', 'get_total', 'get_total_profit')
    inlines = [SaleItemInline]

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity_purchased', 'cost_per_piece', 'supplier_name', 'created_at')
    ordering = ('-created_at',)