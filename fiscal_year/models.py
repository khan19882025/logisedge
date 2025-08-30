from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date


class FiscalYear(models.Model):
    """Model for managing fiscal years"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('closed', 'Closed'),
    ]
    
    name = models.CharField(max_length=100, help_text="Fiscal year name (e.g., FY 2024-25)")
    start_date = models.DateField(help_text="Start date of the fiscal year")
    end_date = models.DateField(help_text="End date of the fiscal year")
    is_current = models.BooleanField(default=False, help_text="Mark as current fiscal year")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    description = models.TextField(blank=True, help_text="Additional description or notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Fiscal Year'
        verbose_name_plural = 'Fiscal Years'
    
    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"
    
    def clean(self):
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError("End date must be after start date")
            
            # Check for overlapping fiscal years
            overlapping = FiscalYear.objects.filter(
                start_date__lte=self.end_date,
                end_date__gte=self.start_date
            ).exclude(pk=self.pk)
            
            if overlapping.exists():
                raise ValidationError("Fiscal year dates overlap with existing fiscal year")
    
    def save(self, *args, **kwargs):
        # Ensure only one current fiscal year
        if self.is_current:
            FiscalYear.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class FiscalPeriod(models.Model):
    """Model for managing fiscal periods within a fiscal year"""
    
    PERIOD_TYPES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('locked', 'Locked'),
    ]
    
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='periods')
    name = models.CharField(max_length=100, help_text="Period name (e.g., Q1, January)")
    start_date = models.DateField(help_text="Start date of the period")
    end_date = models.DateField(help_text="End date of the period")
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES, default='monthly')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    is_current = models.BooleanField(default=False, help_text="Mark as current period")
    description = models.TextField(blank=True, help_text="Additional description or notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['fiscal_year', 'start_date']
        verbose_name = 'Fiscal Period'
        verbose_name_plural = 'Fiscal Periods'
        unique_together = ['fiscal_year', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.fiscal_year.name}"
    
    def clean(self):
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError("End date must be after start date")
            
            # Check if period is within fiscal year
            if self.fiscal_year:
                if self.start_date < self.fiscal_year.start_date or self.end_date > self.fiscal_year.end_date:
                    raise ValidationError("Period must be within the fiscal year dates")
            
            # Check for overlapping periods within the same fiscal year
            overlapping = FiscalPeriod.objects.filter(
                fiscal_year=self.fiscal_year,
                start_date__lte=self.end_date,
                end_date__gte=self.start_date
            ).exclude(pk=self.pk)
            
            if overlapping.exists():
                raise ValidationError("Period dates overlap with existing period in the same fiscal year")
    
    def save(self, *args, **kwargs):
        # Ensure only one current period per fiscal year
        if self.is_current:
            FiscalPeriod.objects.filter(fiscal_year=self.fiscal_year).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class FiscalSettings(models.Model):
    """Model for fiscal year settings and configuration"""
    
    DEFAULT_FISCAL_YEAR_START_MONTH_CHOICES = [
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
    ]
    
    DEFAULT_PERIOD_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
    ]
    
    default_fiscal_year_start_month = models.IntegerField(
        choices=DEFAULT_FISCAL_YEAR_START_MONTH_CHOICES,
        default=1,
        help_text="Default month for fiscal year start"
    )
    default_period_type = models.CharField(
        max_length=20,
        choices=DEFAULT_PERIOD_TYPE_CHOICES,
        default='monthly',
        help_text="Default period type for new fiscal years"
    )
    auto_create_periods = models.BooleanField(
        default=True,
        help_text="Automatically create periods when creating a new fiscal year"
    )
    allow_overlapping_periods = models.BooleanField(
        default=False,
        help_text="Allow overlapping periods within the same fiscal year"
    )
    require_period_approval = models.BooleanField(
        default=False,
        help_text="Require approval before closing periods"
    )
    fiscal_year_naming_convention = models.CharField(
        max_length=100,
        default="FY {start_year}-{end_year}",
        help_text="Naming convention for fiscal years (use {start_year} and {end_year} placeholders)"
    )
    period_naming_convention = models.CharField(
        max_length=100,
        default="{period_type} {period_number}",
        help_text="Naming convention for periods (use {period_type} and {period_number} placeholders)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Fiscal Settings'
        verbose_name_plural = 'Fiscal Settings'
    
    def __str__(self):
        return "Fiscal Year Settings"
    
    def save(self, *args, **kwargs):
        # Ensure only one settings instance
        if not self.pk and FiscalSettings.objects.exists():
            return
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create the fiscal settings instance"""
        settings, created = cls.objects.get_or_create()
        return settings
