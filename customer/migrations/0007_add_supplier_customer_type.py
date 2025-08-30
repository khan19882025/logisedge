# Generated manually to add Supplier customer type

from django.db import migrations

def add_supplier_customer_type(apps, schema_editor):
    CustomerType = apps.get_model('customer', 'CustomerType')
    
    # Check if Supplier already exists to avoid duplicates
    if not CustomerType.objects.filter(code='SUP').exists():
        CustomerType.objects.create(
            name='Supplier',
            code='SUP',
            description='Supplier or vendor for goods and services'
        )

def remove_supplier_customer_type(apps, schema_editor):
    CustomerType = apps.get_model('customer', 'CustomerType')
    CustomerType.objects.filter(code='SUP').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0006_customer_salesman'),
    ]

    operations = [
        migrations.RunPython(add_supplier_customer_type, remove_supplier_customer_type),
    ] 