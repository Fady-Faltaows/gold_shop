from django import forms
from .models import Customer, Expense, Sale, SaleItem, SaleReturn, Product, GoldPrice, Purchase, Category, Supplier


class GoldPriceForm(forms.ModelForm):
    class Meta:
        model = GoldPrice
        fields = ['price_per_gram']
        widgets = {
            'price_per_gram': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter new gold price per gram',
                'step': '0.01'
            })
        }


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['customer', 'customer_name', 'discount_amount', 'notes']
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select'
            }),
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Walk-in customer name (optional)'
            }),
            'discount_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.filter(status__in=['prospect', 'active'])
        self.fields['customer'].required = False


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'full_name',
            'customer_type',
            'status',
            'phone',
            'email',
            'address',
            'date_of_birth',
            'acquisition_source',
            'notes',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer full name'}),
            'customer_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'acquisition_source': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Referral, walk-in, social media...'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'name',
            'contact_person',
            'phone',
            'email',
            'address',
            'tax_number',
            'payment_terms',
            'lead_time_days',
            'notes',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supplier name'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact person'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'tax_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tax number'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Payment terms'}),
            'lead_time_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['product', 'quantity_purchased', 'supplier', 'supplier_name', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select', 'id': 'id_product'}),
            'quantity_purchased': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'supplier_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'One-time supplier name (optional)'
            }),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # add data attributes to each product option
        self.fields['product'].queryset = Product.objects.select_related('category').all()
        choices = [('', '— Select Product —')]
        for p in Product.objects.all():
            choices.append((p.id, f"{p.name} ({p.karat}K - {p.weight_grams}g)"))
        self.fields['product'].widget.choices = choices
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)
        self.fields['supplier'].required = False

    class Media:
        pass


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['sku', 'barcode', 'name', 'category', 'preferred_supplier', 'karat', 'weight_grams', 'workmanship_fee', 'low_stock_threshold', 'image', 'notes']
        widgets = {
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SKU (optional)'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Barcode (optional)'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Product name'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'karat': forms.Select(attrs={
                'class': 'form-select'
            }),
            'preferred_supplier': forms.Select(attrs={
                'class': 'form-select'
            }),
            'weight_grams': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'workmanship_fee': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'low_stock_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['preferred_supplier'].queryset = Supplier.objects.filter(is_active=True)
        self.fields['preferred_supplier'].required = False

    def clean_sku(self):
        return self.cleaned_data.get('sku') or None

    def clean_barcode(self):
        return self.cleaned_data.get('barcode') or None


class SaleReturnForm(forms.ModelForm):
    class Meta:
        model = SaleReturn
        fields = ['sale_item', 'quantity', 'refund_amount', 'restock', 'reason']
        widgets = {
            'sale_item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'refund_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01'}),
            'restock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['branch', 'category', 'description', 'amount', 'paid_at', 'notes']
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Expense description'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01'}),
            'paid_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
