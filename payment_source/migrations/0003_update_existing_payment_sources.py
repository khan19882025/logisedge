# Generated manually for updating existing PaymentSource records

from django.db import migrations, models


def update_existing_payment_sources(apps, schema_editor):
    """Update existing PaymentSource records with default payment types and linked accounts"""
    PaymentSource = apps.get_model('payment_source', 'PaymentSource')
    ChartOfAccount = apps.get_model('chart_of_accounts', 'ChartOfAccount')
    Company = apps.get_model('company', 'Company')
    
    # Get the first active company
    try:
        company = Company.objects.filter(is_active=True).first()
        if not company:
            print("No active company found, skipping payment source updates")
            return
    except Exception as e:
        print(f"Error getting company: {e}")
        return
    
    # Define the default mapping for existing payment sources
    default_mapping = {
        'Vendor': {
            'payment_type': 'postpaid',
            'account_keywords': ['payable', 'vendor', 'supplier']
        },
        'Credit Card': {
            'payment_type': 'postpaid',
            'account_keywords': ['credit', 'card', 'payable']
        },
        'DP World': {
            'payment_type': 'prepaid',
            'account_keywords': ['prepaid', 'deposit', 'dp world']
        },
        'CDR Account': {
            'payment_type': 'prepaid',
            'account_keywords': ['prepaid', 'cdr', 'deposit']
        },
        'Petty Cash': {
            'payment_type': 'cash_bank',
            'account_keywords': ['petty', 'cash', 'bank']
        },
        'Bank': {
            'payment_type': 'cash_bank',
            'account_keywords': ['bank', 'current', 'account']
        },
        'Late Manifest': {
            'payment_type': 'postpaid',
            'account_keywords': ['payable', 'late', 'manifest']
        }
    }
    
    # Update existing payment sources
    for payment_source in PaymentSource.objects.all():
        name_lower = payment_source.name.lower()
        
        # Find matching default mapping
        matched_mapping = None
        for key, mapping in default_mapping.items():
            if key.lower() in name_lower:
                matched_mapping = mapping
                break
        
        if matched_mapping:
            # Update payment type
            payment_source.payment_type = matched_mapping['payment_type']
            
            # Try to find and link appropriate account
            if not payment_source.linked_account:
                account_keywords = matched_mapping['account_keywords']
                
                # Search for appropriate account based on payment type and keywords
                if matched_mapping['payment_type'] == 'prepaid':
                    # Look for asset accounts
                    account = ChartOfAccount.objects.filter(
                        company=company,
                        account_type__category='ASSET',
                        is_active=True
                    ).filter(
                        models.Q(name__icontains=account_keywords[0]) |
                        models.Q(name__icontains=account_keywords[1]) if len(account_keywords) > 1 else models.Q(name__icontains=account_keywords[0])
                    ).first()
                elif matched_mapping['payment_type'] == 'postpaid':
                    # Look for liability accounts
                    account = ChartOfAccount.objects.filter(
                        company=company,
                        account_type__category='LIABILITY',
                        is_active=True
                    ).filter(
                        models.Q(name__icontains=account_keywords[0]) |
                        models.Q(name__icontains=account_keywords[1]) if len(account_keywords) > 1 else models.Q(name__icontains=account_keywords[0])
                    ).first()
                elif matched_mapping['payment_type'] == 'cash_bank':
                    # Look for asset accounts (bank/cash)
                    account = ChartOfAccount.objects.filter(
                        company=company,
                        account_type__category='ASSET',
                        is_active=True
                    ).filter(
                        models.Q(name__icontains=account_keywords[0]) |
                        models.Q(name__icontains=account_keywords[1]) if len(account_keywords) > 1 else models.Q(name__icontains=account_keywords[0])
                    ).first()
                else:
                    account = None
                
                if account:
                    payment_source.linked_account = account
            
            payment_source.save()
            print(f"Updated {payment_source.name} with payment_type={payment_source.payment_type}")


def reverse_update_existing_payment_sources(apps, schema_editor):
    """Reverse the payment source updates"""
    PaymentSource = apps.get_model('payment_source', 'PaymentSource')
    
    # Reset payment_type to default and clear linked_account
    PaymentSource.objects.all().update(
        payment_type='postpaid',
        linked_account=None
    )


class Migration(migrations.Migration):

    dependencies = [
        ('payment_source', '0002_auto_20250814_1621'),
        ('chart_of_accounts', '0001_initial'),
        ('company', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            update_existing_payment_sources,
            reverse_update_existing_payment_sources
        ),
    ]
