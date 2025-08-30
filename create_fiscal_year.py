#!/usr/bin/env python
import os
import sys
import django
from datetime import date

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logisEdge.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from fiscal_year.models import FiscalYear

print("=== CREATING FISCAL YEAR 2025 ===")

# Check if fiscal year 2025 already exists
existing_fy = FiscalYear.objects.filter(name__icontains="2025").first()
if existing_fy:
    print(f"✅ Fiscal Year 2025 already exists: {existing_fy.name}")
    print(f"   Start Date: {existing_fy.start_date}")
    print(f"   End Date: {existing_fy.end_date}")
    print(f"   Status: {existing_fy.status}")
    print(f"   Is Current: {existing_fy.is_current}")
else:
    # Create fiscal year 2025
    fiscal_year = FiscalYear.objects.create(
        name="FY 2025",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        is_current=True,
        status='active',
        description="Fiscal Year 2025 - Calendar Year"
    )
    print(f"✅ Created Fiscal Year: {fiscal_year.name}")
    print(f"   Start Date: {fiscal_year.start_date}")
    print(f"   End Date: {fiscal_year.end_date}")
    print(f"   Status: {fiscal_year.status}")
    print(f"   Is Current: {fiscal_year.is_current}")

print("\n=== FISCAL YEAR SETUP COMPLETE ===")