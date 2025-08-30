# Generated migration to fix null customer codes

from django.db import migrations

def fix_null_customer_codes(apps, schema_editor):
    Customer = apps.get_model('customer', 'Customer')
    CustomerType = apps.get_model('customer', 'CustomerType')
    
    # Get all customers with null customer codes
    customers_without_codes = Customer.objects.filter(customer_code__isnull=True)
    
    for customer in customers_without_codes:
        # Get the first customer type (primary type)
        primary_type = customer.customer_types.first()
        if primary_type:
            type_prefix = primary_type.code[:3].upper()
        else:
            type_prefix = "CUS"  # Default prefix
        
        # Find the highest number for this exact prefix
        import re
        pattern = f"^{re.escape(type_prefix)}(\\d+)$"
        
        customers_with_prefix = Customer.objects.filter(
            customer_code__regex=pattern
        ).exclude(pk=customer.pk)
        
        max_number = 0
        for existing_customer in customers_with_prefix:
            if existing_customer.customer_code:
                try:
                    number = int(existing_customer.customer_code[len(type_prefix):])
                    max_number = max(max_number, number)
                except ValueError:
                    continue
        
        new_number = max_number + 1
        
        # Generate unique code and check for conflicts
        while True:
            new_code = f"{type_prefix}{new_number:04d}"
            if not Customer.objects.filter(customer_code=new_code).exclude(pk=customer.pk).exists():
                customer.customer_code = new_code
                customer.save(update_fields=['customer_code'])
                break
            new_number += 1

def reverse_fix_null_customer_codes(apps, schema_editor):
    # This migration is not reversible as we don't want to set codes back to null
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('customer', '0008_alter_customer_customer_code'),
    ]
    
    operations = [
        migrations.RunPython(fix_null_customer_codes, reverse_fix_null_customer_codes),
    ]