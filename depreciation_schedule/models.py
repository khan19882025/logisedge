from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from asset_register.models import Asset
from chart_of_accounts.models import ChartOfAccount
from general_journal.models import JournalEntry, JournalEntryLine
from fiscal_year.models import FiscalYear


class DepreciationSchedule(models.Model):
    """Model for Depreciation Schedule"""
    SCHEDULE_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule_number = models.CharField(max_length=50, unique=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Date Range
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Financial Settings
    depreciation_expense_account = models.ForeignKey(
        ChartOfAccount, 
        on_delete=models.PROTECT, 
        related_name='depreciation_expense_schedules',
        help_text="Account to debit for depreciation expense"
    )
    accumulated_depreciation_account = models.ForeignKey(
        ChartOfAccount, 
        on_delete=models.PROTECT, 
        related_name='accumulated_depreciation_schedules',
        help_text="Account to credit for accumulated depreciation"
    )
    
    # Status and Totals
    status = models.CharField(max_length=20, choices=SCHEDULE_STATUS_CHOICES, default='draft')
    total_depreciation = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_assets = models.IntegerField(default=0)
    
    # Journal Entry Reference
    journal_entry = models.ForeignKey(
        JournalEntry, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='depreciation_schedules'
    )
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_depreciation_schedules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='updated_depreciation_schedules', null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_depreciation_schedules')
    posted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Depreciation Schedule'
        verbose_name_plural = 'Depreciation Schedules'
    
    def __str__(self):
        return f"{self.schedule_number} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.schedule_number:
            self.schedule_number = self.generate_schedule_number()
        super().save(*args, **kwargs)
    
    def generate_schedule_number(self):
        """Generate unique schedule number"""
        year = self.start_date.year
        month = self.start_date.month
        last_schedule = DepreciationSchedule.objects.filter(
            schedule_number__startswith=f'DS-{year}-{month:02d}-'
        ).order_by('-schedule_number').first()
        
        if last_schedule:
            try:
                last_number = int(last_schedule.schedule_number.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f'DS-{year}-{month:02d}-{new_number:04d}'
    
    def calculate_depreciation(self):
        """Calculate depreciation for all eligible assets"""
        # Clear existing calculations
        self.depreciation_entries.all().delete()
        
        # Get eligible assets
        assets = Asset.objects.filter(
            is_deleted=False,
            disposal_date__isnull=True,
            purchase_value__gt=0,
            useful_life_years__gt=0
        )
        
        total_depreciation = Decimal('0.00')
        total_assets = 0
        
        for asset in assets:
            entries = self.calculate_asset_depreciation(asset)
            if entries:
                total_depreciation += sum(entry.depreciation_amount for entry in entries)
                total_assets += 1
        
        self.total_depreciation = total_depreciation
        self.total_assets = total_assets
        self.status = 'calculated'
        self.save()
        
        return total_depreciation
    
    def calculate_asset_depreciation(self, asset):
        """Calculate depreciation for a specific asset"""
        entries = []
        current_date = self.start_date
        
        while current_date <= self.end_date:
            # Check if asset is eligible for depreciation on this date
            if self.is_asset_eligible_for_depreciation(asset, current_date):
                depreciation_amount = self.calculate_monthly_depreciation(asset, current_date)
                
                if depreciation_amount > 0:
                    entry = DepreciationEntry.objects.create(
                        schedule=self,
                        asset=asset,
                        period=current_date.replace(day=1),
                        opening_value=asset.book_value,
                        depreciation_amount=depreciation_amount,
                        accumulated_depreciation=asset.accumulated_depreciation + depreciation_amount,
                        closing_value=asset.book_value - depreciation_amount
                    )
                    entries.append(entry)
            
            # Move to next month
            current_date = current_date + relativedelta(months=1)
        
        return entries
    
    def is_asset_eligible_for_depreciation(self, asset, date):
        """Check if asset is eligible for depreciation on given date"""
        # Asset must be purchased before or on the date
        if asset.created_at.date() > date:
            return False
        
        # Asset must not be disposed
        if asset.disposal_date and asset.disposal_date <= date:
            return False
        
        # Asset must not be fully depreciated
        if asset.book_value <= asset.salvage_value:
            return False
        
        return True
    
    def calculate_monthly_depreciation(self, asset, date):
        """Calculate monthly depreciation for an asset"""
        if asset.depreciation_method.method == 'straight_line':
            return self.calculate_straight_line_depreciation(asset, date)
        elif asset.depreciation_method.method == 'declining_balance':
            return self.calculate_declining_balance_depreciation(asset, date)
        else:
            return Decimal('0.00')
    
    def calculate_straight_line_depreciation(self, asset, date):
        """Calculate straight-line depreciation"""
        depreciable_amount = asset.purchase_value - asset.salvage_value
        useful_life_months = asset.useful_life_years * 12
        
        if useful_life_months <= 0:
            return Decimal('0.00')
        
        monthly_depreciation = depreciable_amount / useful_life_months
        
        # Check if this would exceed the remaining book value
        remaining_value = asset.book_value - asset.salvage_value
        if monthly_depreciation > remaining_value:
            monthly_depreciation = remaining_value
        
        return monthly_depreciation.quantize(Decimal('0.01'))
    
    def calculate_declining_balance_depreciation(self, asset, date):
        """Calculate declining balance depreciation"""
        rate = asset.depreciation_method.rate_percentage / 100 / 12  # Monthly rate
        depreciation = asset.book_value * rate
        
        # Ensure we don't depreciate below salvage value
        remaining_value = asset.book_value - asset.salvage_value
        if depreciation > remaining_value:
            depreciation = remaining_value
        
        return depreciation.quantize(Decimal('0.01'))
    
    def post_to_general_ledger(self, user):
        """Post depreciation to general ledger"""
        if self.status != 'calculated':
            return False, "Schedule must be calculated before posting"
        
        if self.total_depreciation <= 0:
            return False, "No depreciation to post"
        
        # Create journal entry
        journal_entry = JournalEntry.objects.create(
            date=self.end_date,
            reference=f"Depreciation Schedule {self.schedule_number}",
            description=f"Monthly depreciation for {self.start_date.strftime('%B %Y')}",
            status='draft',
            company=self.depreciation_expense_account.company,
            fiscal_year=self.get_fiscal_year(),
            created_by=user
        )
        
        # Create journal entry lines
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            account=self.depreciation_expense_account,
            description=f"Depreciation expense for {self.start_date.strftime('%B %Y')}",
            debit_amount=self.total_depreciation,
            credit_amount=Decimal('0.00')
        )
        
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            account=self.accumulated_depreciation_account,
            description=f"Accumulated depreciation for {self.start_date.strftime('%B %Y')}",
            debit_amount=Decimal('0.00'),
            credit_amount=self.total_depreciation
        )
        
        # Post the journal entry
        if journal_entry.post(user):
            self.journal_entry = journal_entry
            self.status = 'posted'
            self.posted_by = user
            self.posted_at = timezone.now()
            self.save()
            
            # Update asset records
            self.update_asset_records()
            
            return True, "Depreciation posted successfully"
        else:
            journal_entry.delete()
            return False, "Failed to post journal entry"
    
    def update_asset_records(self):
        """Update asset accumulated depreciation and book values"""
        for entry in self.depreciation_entries.all():
            asset = entry.asset
            asset.accumulated_depreciation = entry.accumulated_depreciation
            asset.book_value = entry.closing_value
            asset.save()
    
    def get_fiscal_year(self):
        """Get the fiscal year for the schedule period"""
        try:
            return FiscalYear.objects.filter(
                start_date__lte=self.start_date,
                end_date__gte=self.end_date
            ).first()
        except:
            return None


class DepreciationEntry(models.Model):
    """Individual depreciation entries for assets"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(DepreciationSchedule, on_delete=models.CASCADE, related_name='depreciation_entries')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='depreciation_entries')
    
    # Period and Values
    period = models.DateField(help_text="Period (YYYY-MM-01)")
    opening_value = models.DecimalField(max_digits=15, decimal_places=2)
    depreciation_amount = models.DecimalField(max_digits=15, decimal_places=2)
    accumulated_depreciation = models.DecimalField(max_digits=15, decimal_places=2)
    closing_value = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['asset__asset_code', 'period']
        unique_together = ['schedule', 'asset', 'period']
        verbose_name = 'Depreciation Entry'
        verbose_name_plural = 'Depreciation Entries'
    
    def __str__(self):
        return f"{self.asset.asset_code} - {self.period.strftime('%Y-%m')} - {self.depreciation_amount}"
    
    @property
    def period_display(self):
        """Display period in YYYY-MM format"""
        return self.period.strftime('%Y-%m')


class DepreciationSettings(models.Model):
    """Settings for depreciation calculations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Default Accounts
    default_depreciation_expense_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        related_name='default_depreciation_expense_settings',
        null=True,
        blank=True,
        help_text="Default account for depreciation expense"
    )
    default_accumulated_depreciation_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.PROTECT,
        related_name='default_accumulated_depreciation_settings',
        null=True,
        blank=True,
        help_text="Default account for accumulated depreciation"
    )
    
    # Calculation Settings
    auto_post_to_gl = models.BooleanField(default=False, help_text="Automatically post to general ledger")
    require_approval = models.BooleanField(default=True, help_text="Require approval before posting")
    minimum_depreciation_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.01,
        help_text="Minimum depreciation amount to post"
    )
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_depreciation_settings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='updated_depreciation_settings', null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Depreciation Setting'
        verbose_name_plural = 'Depreciation Settings'
    
    def __str__(self):
        return "Depreciation Settings"
    
    @classmethod
    def get_settings(cls):
        """Get or create settings"""
        settings, created = cls.objects.get_or_create(
            defaults={
                'created_by': User.objects.first()
            }
        )
        return settings
