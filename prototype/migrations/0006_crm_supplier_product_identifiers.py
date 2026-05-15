# Generated manually to safely backfill unique product identifiers.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import prototype.models


def populate_product_codes(apps, schema_editor):
    Product = apps.get_model('prototype', 'Product')
    for product in Product.objects.all().order_by('pk'):
        if not product.product_code:
            product.product_code = f"PRD-{product.pk:06d}"
            product.save(update_fields=['product_code'])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('prototype', '0005_branch_alter_inventory_product_inventory_branch_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_code', models.CharField(default=prototype.models.generate_customer_code, editable=False, max_length=32, unique=True)),
                ('full_name', models.CharField(max_length=200)),
                ('customer_type', models.CharField(choices=[('individual', 'Individual'), ('business', 'Business')], default='individual', max_length=20)),
                ('status', models.CharField(choices=[('prospect', 'Prospect'), ('active', 'Active'), ('inactive', 'Inactive')], default='active', max_length=20)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('address', models.TextField(blank=True)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('acquisition_source', models.CharField(blank=True, max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('supplier_code', models.CharField(default=prototype.models.generate_supplier_code, editable=False, max_length=32, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('contact_person', models.CharField(blank=True, max_length=200)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('address', models.TextField(blank=True)),
                ('tax_number', models.CharField(blank=True, max_length=100)),
                ('payment_terms', models.CharField(blank=True, max_length=200)),
                ('lead_time_days', models.PositiveIntegerField(default=0)),
                ('notes', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='product_code',
            field=models.CharField(blank=True, editable=False, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='sku',
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='product',
            name='barcode',
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='product',
            name='preferred_supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='prototype.supplier'),
        ),
        migrations.RunPython(populate_product_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='product',
            name='product_code',
            field=models.CharField(default=prototype.models.generate_product_code, editable=False, max_length=32, unique=True),
        ),
        migrations.AddField(
            model_name='sale',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sales', to='prototype.customer'),
        ),
        migrations.CreateModel(
            name='CustomerInteraction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interaction_type', models.CharField(choices=[('call', 'Call'), ('visit', 'Visit'), ('message', 'Message'), ('email', 'Email'), ('complaint', 'Complaint'), ('follow_up', 'Follow-up'), ('other', 'Other')], default='other', max_length=20)),
                ('subject', models.CharField(max_length=200)),
                ('notes', models.TextField(blank=True)),
                ('follow_up_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('branch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='prototype.branch')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interactions', to='prototype.customer')),
            ],
        ),
        migrations.AddField(
            model_name='purchase',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='purchases', to='prototype.supplier'),
        ),
    ]
