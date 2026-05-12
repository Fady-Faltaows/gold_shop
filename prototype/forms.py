from django import forms
from .models import Sale, SaleItem, Product, GoldPrice, Purchase, Category


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
        fields = ['customer_name', 'notes']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Customer name (optional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['product', 'quantity_purchased', 'supplier_name', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select', 'id': 'id_product'}),
            'quantity_purchased': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'supplier_name': forms.TextInput(attrs={'class': 'form-control'}),
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
        fields = ['name', 'category', 'karat', 'weight_grams', 'workmanship_fee', 'image', 'notes']
        widgets = {
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
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }