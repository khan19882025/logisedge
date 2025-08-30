#!/usr/bin/env python
"""
Create a supplier bill for Waseem Transport to test the filtering
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logisEdge.settings')
django.setup()

from supplier_bills.models import SupplierBill
from decimal import Decimal
from datetime import date

print("Creating Supplier Bill for Waseem Transport")
print("=" * 50)

try:
    # Create a supplier bill for Waseem Transport (who has cost transactions)
    bill_data = {
        'supplier': 'Waseem Transport',
        'bill_date': date.today(),
        'due_date': date.today(),
        'amount': Decimal('750.00'),
        'status': 'draft',
        'description': 'Test vendor bill for cost settlement'
    }
    
    bill = SupplierBill.objects.create(**bill_data)
    
    print(f"✅ Created supplier bill: {bill.number}")
    print(f"   Supplier: {bill.supplier}")
    print(f"   Amount: ${bill.amount}")
    print(f"   Status: {bill.status}")
    print(f"   Date: {bill.bill_date}")
    
    print(f"\nNow the pending bills list should show this bill for 'Waseem Transport'")
    print(f"since Waseem Transport has cost transactions in invoices.")
    print(f"\nBills for '3rd Generation' should still be hidden since that")
    print(f"vendor has no cost transactions.")
    
except Exception as e:
    print(f"Error creating supplier bill: {e}")
    import traceback
    traceback.print_exc()