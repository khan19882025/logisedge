# Generated migration to fix decimal/float type issues

from django.db import migrations
from decimal import Decimal

def fix_decimal_values(apps, schema_editor):
    """Convert any float values to proper Decimal values"""
    PettyCashDay = apps.get_model('petty_cash', 'PettyCashDay')
    
    # Update any records that might have float values
    for day in PettyCashDay.objects.all():
        # Ensure opening_balance is Decimal
        if isinstance(day.opening_balance, float) or day.opening_balance is None:
            day.opening_balance = Decimal('0.00')
        
        # Ensure total_expenses is Decimal
        if isinstance(day.total_expenses, float) or day.total_expenses is None:
            day.total_expenses = Decimal('0.00')
        
        # Recalculate closing_balance to ensure it's also Decimal
        day.closing_balance = day.opening_balance - day.total_expenses
        day.save()

def reverse_fix_decimal_values(apps, schema_editor):
    """Reverse migration - no action needed"""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('petty_cash', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(fix_decimal_values, reverse_fix_decimal_values),
    ]