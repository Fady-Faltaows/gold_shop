from django.contrib import admin
from .models import (
    Branch,
    Category,
    Customer,
    CustomerInteraction,
    Expense,
    GoldPrice,
    Inventory,
    Product,
    Purchase,
    Sale,
    SaleItem,
    SaleReturn,
    Supplier,
    UserProfile,
)

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display  = ('name', 'address', 'phone', 'is_active', 'created_at')
    search_fields = ('name',)
    list_filter   = ('is_active',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'role', 'created_at')
    list_filter   = ('role',)
    search_fields = ('user__username',)

@admin.register(GoldPrice)
class GoldPriceAdmin(admin.ModelAdmin):
    list_display = ('price_per_gram', 'updated_at')
    ordering     = ('-updated_at',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'description')
    search_fields = ('name',)


class CustomerInteractionInline(admin.TabularInline):
    model = CustomerInteraction
    extra = 0
    fields = ('interaction_type', 'subject', 'branch', 'follow_up_at', 'created_by', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display  = ('customer_code', 'full_name', 'customer_type', 'status', 'phone', 'email', 'created_at')
    list_filter   = ('customer_type', 'status', 'created_at')
    search_fields = ('customer_code', 'full_name', 'phone', 'email')
    readonly_fields = ('customer_code', 'created_at', 'updated_at')
    inlines       = [CustomerInteractionInline]


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display  = ('supplier_code', 'name', 'contact_person', 'phone', 'email', 'is_active', 'lead_time_days')
    list_filter   = ('is_active',)
    search_fields = ('supplier_code', 'name', 'contact_person', 'phone', 'email', 'tax_number')
    readonly_fields = ('supplier_code', 'created_at', 'updated_at')


@admin.register(CustomerInteraction)
class CustomerInteractionAdmin(admin.ModelAdmin):
    list_display  = ('customer', 'interaction_type', 'subject', 'branch', 'follow_up_at', 'created_by', 'created_at')
    list_filter   = ('interaction_type', 'branch', 'created_at')
    search_fields = ('customer__full_name', 'customer__customer_code', 'subject', 'notes')
    autocomplete_fields = ('customer', 'created_by')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ('product_code', 'sku', 'barcode', 'name', 'category', 'preferred_supplier', 'karat', 'weight_grams', 'workmanship_fee', 'low_stock_threshold', 'get_selling_price')
    list_filter   = ('karat', 'category', 'preferred_supplier')
    search_fields = ('product_code', 'sku', 'barcode', 'name')
    readonly_fields = ('product_code',)
    ordering      = ('category', 'name')


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display  = ('product', 'quantity_pieces')
    search_fields = ('product__name',)
    ordering      = ('product',)


class SaleItemInline(admin.TabularInline):
    model          = SaleItem
    extra          = 1
    fields         = ('product', 'quantity', 'price_per_piece', 'cost_per_piece', 'get_subtotal', 'get_profit')
    readonly_fields = ('price_per_piece', 'cost_per_piece', 'get_subtotal', 'get_profit')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display   = ('id', 'customer', 'customer_name', 'discount_amount', 'gold_price_at_sale', 'get_total', 'get_total_profit', 'created_at')
    search_fields  = ('customer__full_name', 'customer__customer_code', 'customer_name')
    ordering       = ('-created_at',)
    readonly_fields = ('gold_price_at_sale', 'get_total', 'get_total_profit')
    inlines        = [SaleItemInline]


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity_purchased', 'cost_per_piece', 'supplier', 'supplier_name', 'created_at')
    search_fields = ('product__name', 'product__product_code', 'supplier__name', 'supplier__supplier_code', 'supplier_name')
    ordering     = ('-created_at',)


@admin.register(SaleReturn)
class SaleReturnAdmin(admin.ModelAdmin):
    list_display = ('sale_item', 'branch', 'quantity', 'refund_amount', 'restock', 'created_at')
    list_filter = ('restock', 'branch', 'created_at')
    search_fields = ('sale_item__product__name', 'sale_item__sale__id')
    ordering = ('-created_at',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'category', 'branch', 'amount', 'paid_at')
    list_filter = ('category', 'branch', 'paid_at')
    search_fields = ('description', 'notes')
    ordering = ('-paid_at',)
