# Generated manually for populating new PaymentSource fields

from django.db import migrations


def populate_new_fields(apps, schema_editor):
    """Populate new fields from existing data"""
    PaymentSource = apps.get_model('payment_source', 'PaymentSource')
    
    for payment_source in PaymentSource.objects.all():
        # Set linked_ledger from linked_account if available
        if payment_source.linked_account and not payment_source.linked_ledger:
            payment_source.linked_ledger = payment_source.linked_account
        
        # Set source_type from payment_type
        if payment_source.payment_type == 'prepaid':
            payment_source.source_type = 'prepaid'
        elif payment_source.payment_type == 'postpaid':
            payment_source.source_type = 'postpaid'
        else:
            payment_source.source_type = 'postpaid'  # Default
        
        # Set category based on payment_type
        if payment_source.payment_type == 'cash_bank':
            payment_source.category = 'bank'
        else:
            payment_source.category = 'other_payable'  # Default
        
        # Set active from is_active
        payment_source.active = payment_source.is_active
        
        # Set default currency to AED (ID 3 based on the codebase)
        if not payment_source.currency:
            try:
                from multi_currency.models import Currency
                aed_currency = Currency.objects.filter(code='AED').first()
                if aed_currency:
                    payment_source.currency = aed_currency
            except:
                pass  # Skip if currency model is not available
        
        payment_source.save()


def reverse_populate_new_fields(apps, schema_editor):
    """Reverse the population of new fields"""
    PaymentSource = apps.get_model('payment_source', 'PaymentSource')
    
    for payment_source in PaymentSource.objects.all():
        # Reset fields to defaults
        payment_source.source_type = 'postpaid'
        payment_source.category = 'other_payable'
        payment_source.active = True
        payment_source.save()


class Migration(migrations.Migration):

    dependencies = [
        ('payment_source', '0004_paymentsource_active_paymentsource_category_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_new_fields, reverse_populate_new_fields),
    ]
