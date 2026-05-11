from django import forms
from .models import Sale, SaleItem, Product, GoldPrice, Purchase

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['customer_name', 'notes']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer name (optional)'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select product-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

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

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['product', 'quantity_purchased', 'cost_per_piece', 'supplier_name', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity_purchased': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'cost_per_piece': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'supplier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }